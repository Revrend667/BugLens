from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

class SlackScanner:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def fetch_messages(self, channel: str, cursor: str = None):
        """
        Fetch messages from a channel using conversations.history
        """
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
        """
        Fetch all messages in a channel, including thread replies recursively
        """
        messages, cursor = self.fetch_messages(channel)
        all_messages = []

        def extract_text(msg):
            """
            Combine message text and unfurled attachments
            """
            text_parts = [msg.get('text', '')]
            for att in msg.get('attachments', []):
                if att.get('is_msg_unfurl') or att.get('fallback'):
                    text_parts.append(att.get('fallback', ''))
            return "\n".join(filter(None, text_parts))

        def dfs(msg):
            """
            Recursive DFS for threads
            """
            all_messages.append(extract_text(msg))

            # If message is thread root and has replies
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
