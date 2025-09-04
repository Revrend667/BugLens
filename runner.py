import argparse
from processor import SlackProcessor
from logger import logger


def main():
    parser = argparse.ArgumentParser(description="Slack Channel Analyzer")
    parser.add_argument("--channel", required=True, help="Slack channel ID")
    parser.add_argument("--bedrock-model-id", required=True, help="Bedrock model ID")
    parser.add_argument("--slack-token", required=True, help="Slack Bot Token")
    parser.add_argument("--jira-user", required=False, help="JIRA Email / Username")
    parser.add_argument("--jira-token", required=False, help="JIRA API Token")
    parser.add_argument(
        "--jira-server",
        required=False,
        help="JIRA Server URL (https://<company>.atlassian.net)",
    )
    args = parser.parse_args()

    processor = SlackProcessor(
        slack_token=args.slack_token,
        bedrock_model_id=args.bedrock_model_id,
        jira_user=args.jira_user,
        jira_token=args.jira_token,
        jira_server=args.jira_server,
    )

    summary = processor.process_channel(args.channel)
    logger.info("=== RCA and Learnings ===")
    print(summary)


if __name__ == "__main__":
    main()
