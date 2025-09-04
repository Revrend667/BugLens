from bedrock_client import BedrockClient
from jira_client import JiraClient
from logger import logger
from slack_scanner import SlackScanner


class SlackProcessor:
    def __init__(
        self,
        slack_token,
        bedrock_model_id,
        jira_user=None,
        jira_token=None,
        jira_server=None,
    ):
        # Create JiraClient if credentials are provided
        jira_client = JiraClient(server=jira_server, user=jira_user, token=jira_token)

        # Pass JiraClient instance to SlackScanner
        self.slack_scanner = SlackScanner(token=slack_token, jira_client=jira_client)
        self.bedrock = BedrockClient(model_id=bedrock_model_id)

    def process_channel(self, channel_id: str) -> str:
        messages = self.slack_scanner.fetch_all_messages_dfs(channel_id)
        prompt = "\n\n".join(messages)
        if not prompt:
            logger.info("No messages found in channel.")
            return ""
        print(messages)
        summary = self.bedrock.summarize(prompt)
        return summary
