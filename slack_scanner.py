import logging
import re

import requests
from slack_sdk import WebClient

from jira_client import JiraClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

USER_MENTION_RE = re.compile(r"<@[\w]+>")
JIRA_LINK_RE = re.compile(r"https?://([\w\-]+)\.atlassian\.net/browse/([\w\-]+-\d+)")
SYSTEM_SUBTYPES = ["channel_join", "channel_leave"]


class SlackScanner:
    def __init__(self, token: str, jira_client: JiraClient = None):
        self.client = WebClient(token=token)
        self.jira_client = jira_client

    def fetch_messages(self, channel: str):
        """Fetch all messages incrementally with logging."""
        all_messages = []
        cursor = None
        page = 1

        while True:
            try:
                logger.info(f"Fetching page {page} of messages")
                resp = self.client.conversations_history(
                    channel=channel, cursor=cursor, limit=200
                )
                messages = resp.get("messages", [])
                logger.info(f"Fetched {len(messages)} messages in page {page}")
                all_messages.extend(messages)
                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
                page += 1
            except Exception as e:
                logger.error(f"Slack fetch failed at page {page}: {e}")
                break

        logger.info(f"Total messages fetched: {len(all_messages)}")
        return all_messages

    def fetch_file_content(self, file_obj: dict) -> str:
        """Download file content with timeout and logging."""
        url = file_obj.get("url_private")
        if not url:
            return ""
        headers = {"Authorization": f"Bearer {self.client.token}"}
        try:
            logger.info(f"Downloading file: {file_obj.get('name')}")
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.Timeout:
            logger.warning(f"Timeout fetching file {file_obj.get('name')}")
        except requests.RequestException as e:
            logger.error(f"Error downloading file {file_obj.get('name')}: {e}")
        return ""

    def fetch_all_messages_dfs(self, channel: str):
        all_messages = []
        messages = self.fetch_messages(channel)

        def extract_text(msg):
            text_parts = [msg.get("text", "")]

            # Attachments
            for att in msg.get("attachments", []):
                if att.get("fallback"):
                    text_parts.append(att["fallback"])
                for block in att.get("blocks", []):
                    if block.get("type") == "section":
                        text_obj = block.get("text", {})
                        if text_obj.get("text"):
                            text_parts.append(text_obj["text"])
                    elif block.get("type") == "context":
                        for elem in block.get("elements", []):
                            if elem.get("text"):
                                text_parts.append(elem["text"])

            # Files
            for file_obj in msg.get("files", []):
                file_text = self.fetch_file_content(file_obj)
                if file_text:
                    text_parts.append(
                        f"--- Start of file: {file_obj.get('name')} ---\n{file_text}\n--- End of file ---"
                    )

            combined_text = "\n".join(filter(None, text_parts))
            combined_text = USER_MENTION_RE.sub("", combined_text).strip()

            # JIRA expansion
            if self.jira_client:
                for match in JIRA_LINK_RE.finditer(combined_text):
                    _, issue_key = match.groups()
                    jira_details = self.jira_client.fetch_issue(issue_key)
                    if jira_details:
                        combined_text += (
                            f"\n\nJIRA [{issue_key}] Details:\n{jira_details}"
                        )

            return combined_text

        def dfs(msg):
            if msg.get("subtype") in SYSTEM_SUBTYPES:
                return

            text = extract_text(msg)
            if text:
                all_messages.append(text)

            if (
                msg.get("thread_ts") == msg.get("ts")
                and int(msg.get("reply_count", 0)) > 0
            ):
                replies_cursor = None
                while True:
                    try:
                        resp = self.client.conversations_replies(
                            channel=channel,
                            ts=msg["ts"],
                            cursor=replies_cursor,
                            limit=200,
                        )
                        replies = resp.get("messages", [])[1:]  # skip root
                        logger.info(
                            f"Processing {len(replies)} replies for thread {msg['ts']}"
                        )
                        for reply in replies:
                            dfs(reply)
                        replies_cursor = resp.get("response_metadata", {}).get(
                            "next_cursor"
                        )
                        if not replies_cursor:
                            break
                    except Exception as e:
                        logger.error(f"Fetching replies failed: {e}")
                        break

        for idx, m in enumerate(sorted(messages, key=lambda x: float(x["ts"])), 1):
            logger.info(f"Processing message {idx}/{len(messages)} ts={m['ts']}")
            dfs(m)

        logger.info(
            f"Processed total {len(all_messages)} messages including threads and attachments"
        )
        return all_messages
