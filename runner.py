import argparse
import os
from processor import SlackProcessor
from logger import logger

def main():
    parser = argparse.ArgumentParser(description="Slack Channel Analyzer")
    parser.add_argument("--channel", required=True, help="Slack channel ID")
    parser.add_argument("--bedrock-model-id", required=True, help="Bedrock model ID")
    args = parser.parse_args()

    slack_token = os.environ.get("SLACK_TOKEN")
    jira_user = os.environ.get("JIRA_USER")
    jira_token = os.environ.get("JIRA_TOKEN")
    jira_server = os.environ.get("JIRA_SERVER")

    if not slack_token:
        logger.error("SLACK_TOKEN environment variable is missing")
        return

    processor = SlackProcessor(
        slack_token=slack_token,
        bedrock_model_id=args.bedrock_model_id,
        jira_user=jira_user,
        jira_token=jira_token,
        jira_server=jira_server
    )

    summary = processor.process_channel(args.channel)
    logger.info("=== Bedrock Summary / RCA / QA Learnings ===")
    print(summary)

if __name__ == "__main__":
    main()
