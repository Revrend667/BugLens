from bedrock_client import BedrockClient
from slack_scanner import SlackScanner
from logger import logger

class SlackProcessor:
    def __init__(self, slack_token: str, bedrock_model_id: str, jira_user=None, jira_token=None, jira_server=None):
        self.scanner = SlackScanner(slack_token, jira_user, jira_token, jira_server)
        self.bedrock = BedrockClient(model_id=bedrock_model_id)

    def process_channel(self, channel: str):
        messages = self.scanner.fetch_all_messages_dfs(channel)
        combined_text = "\n\n".join(messages)
        logger.info(f"Fetched {len(messages)} messages from channel {channel}")
        summary = self.bedrock.summarize(combined_text)
        return summary
