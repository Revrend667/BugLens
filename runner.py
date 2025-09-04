import argparse
import logging
from slack_scanner import SlackScanner
#from bedrock_client import BedrockClient
#from processor import Processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Slack → Bedrock → Yugaboard Runner')
parser.add_argument('--channel', required=True, help='Slack channel ID to parse')
parser.add_argument('--token', required=True, help='Slack Bot Token')
# parser.add_argument('--bedrock-endpoint', required=True, help='Bedrock API endpoint')
# parser.add_argument('--bedrock-api-key', required=True, help='Bedrock API key')
# parser.add_argument('--confidence-threshold', type=float, default=0.75, help='Confidence threshold for action items')
args = parser.parse_args()

slack = SlackScanner(token=args.token)
# bedrock = BedrockClient(endpoint=args.bedrock_endpoint, api_key=args.bedrock_api_key)
# processor = Processor(threshold=args.confidence_threshold)

logger.info(f"Processing channel: {args.channel}")
messages = slack.fetch_all_messages_dfs(args.channel)
if not messages:
    logger.info("No messages found.")
    exit(0)

print(messages)

# bedrock_response = bedrock.extract(messages)
# summary, items, categories = processor.process(bedrock_response)
# logger.info(f"Summary: {summary}")
# for item in items:
#     logger.info(f"Action Item: {item.title} | Confidence: {item.confidence}")


