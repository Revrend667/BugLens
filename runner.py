import argparse
from slack_scanner import SlackScanner
from bedrock_client import BedrockClient
from logger import logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--slack-token", required=True)
    parser.add_argument("--bedrock-model-id", required=True)
    args = parser.parse_args()

    # Fetch messages from Slack
    scanner = SlackScanner(token=args.slack_token)
    messages = scanner.fetch_all_messages_dfs(args.channel)

    if not messages:
        logger.info("No messages found in Slack channel.")
        return

    print(messages)

    # Send to Bedrock for RCA
    bedrock = BedrockClient(model_id=args.bedrock_model_id)
    rca_summary = bedrock.get_rca(messages)

    print("\n=== Bedrock RCA / QA Learnings ===\n")
    print(rca_summary)

if __name__ == "__main__":
    main()
