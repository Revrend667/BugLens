import re
from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

USER_MENTION_RE = re.compile(r"<@[\w]+>")  # matches <@U02ARQEG6KS>

# List of Slack system message subtypes to skip
SYSTEM_SUBTYPES = [
    "channel_join",
    "channel_leave"
]

class SlackScanner:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def fetch_messages(self, channel: str, cursor: str = None):
        try:
            resp = self.client.conversations_history(
                channel=channel,
                cursor=cursor,
                limit=200
            )
            return resp.get('messages', []), resp.get('response_metadata', {}).get('next_cursor')
        except Exception as e:
            logger.error(f"Slack fetch failed: {e}")
            return [], None

    def fetch_all_messages_dfs(self, channel: str):
        messages, cursor = self.fetch_messages(channel)
        all_messages = []

        def extract_text(msg):
            """
            Combine message text, unfurled attachments, and block text for link previews
            """
            text_parts = [msg.get('text', '')]

            for att in msg.get('attachments', []):
                if att.get('fallback'):
                    text_parts.append(att['fallback'])
                for block in att.get('blocks', []):
                    if block.get('type') == 'section':
                        text_obj = block.get('text', {})
                        if text_obj.get('text'):
                            text_parts.append(text_obj['text'])
                    elif block.get('type') == 'context':
                        for elem in block.get('elements', []):
                            if elem.get('text'):
                                text_parts.append(elem['text'])

            combined_text = "\n".join(filter(None, text_parts))
            # Remove user mentions
            combined_text = USER_MENTION_RE.sub("", combined_text).strip()
            return combined_text

        def dfs(msg):
            # Skip system messages based on subtype
            if msg.get('subtype') in SYSTEM_SUBTYPES:
                return

            text = extract_text(msg)
            if text:
                all_messages.append(text)

            # handle threaded replies
            if msg.get('thread_ts') == msg.get('ts') and int(msg.get('reply_count', 0)) > 0:
                replies_cursor = None
                while True:
                    try:
                        resp = self.client.conversations_replies(
                            channel=channel,
                            ts=msg['ts'],
                            cursor=replies_cursor,
                            limit=200
                        )
                        replies = resp.get('messages', [])[1:]  # skip root
                        for reply in replies:
                            dfs(reply)
                        replies_cursor = resp.get('response_metadata', {}).get('next_cursor')
                        if not replies_cursor:
                            break
                    except Exception as e:
                        logger.error(f"Fetching replies failed: {e}")
                        break

        for m in sorted(messages, key=lambda x: float(x['ts'])):
            dfs(m)

        return all_messages
