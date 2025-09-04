import argparse
from slack_scanner import SlackScanner
from processor import Preprocessor
from bedrock_client import BedrockClient
from logger import logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slack-token", required=True, help="Slack bot token")
    parser.add_argument("--channel", required=True, help="Slack channel ID")
    parser.add_argument("--bedrock-model-id", required=True, help="Bedrock model ID (e.g., 'anthropic.claude-3')")
    args = parser.parse_args()

    scanner = SlackScanner(token=args.slack_token)
    messages = scanner.fetch_all_messages_dfs(args.channel)
    if not messages:
        logger.info("No messages found in channel.")
        return

    pre = Preprocessor()
    prompt = pre.prepare_prompt_payload(messages)

    bedrock = BedrockClient(model_id=args.bedrock_model_id)
    summary = bedrock.summarize(prompt)

    logger.info("=== Bedrock Summary / RCA / QA Learnings ===\n%s", summary)

if __name__ == "__main__":
    main()
