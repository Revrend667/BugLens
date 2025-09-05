# 🔍 BugLens

**BugLens** is a comprehensive tool for analyzing **Slack channel conversations** and generating detailed **Root Cause Analysis (RCA)** and **QA learnings** using **AWS Bedrock AI models**.

## Overview

This tool fetches messages from Slack channels (including threads and file attachments), optionally enriches them with JIRA issue details, and uses AWS Bedrock's AI models to generate structured analysis reports focused on technical learnings and improvements.

## Features

- **Complete Message Extraction**: Fetches all messages from Slack channels including:
  - Regular messages and replies
  - Thread conversations
  - File attachments (with content download)
  - Message attachments and blocks
- **JIRA Integration**: Automatically fetches and includes JIRA issue details for linked tickets
- **AI-Powered Analysis**: Uses AWS Bedrock models to generate structured RCA and QA learnings
- **Chunked Processing**: Handles large message volumes by processing in manageable chunks
- **Multi-level Summarization**: Applies hierarchical summarization for comprehensive analysis

## Architecture

```
runner.py (CLI entry point)
    ↓
processor.py (Main orchestrator)
    ↓
slack_scanner.py (Slack API client)
    ↓
bedrock_client.py (AI analysis)
    ↓
jira_client.py (JIRA integration)
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd BugLens
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials for Bedrock access:
```bash
aws configure
```

## Usage

### Basic Usage

```bash
python runner.py \
  --channel "#incident-channel" \
  --bedrock-model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
  --slack-token "xoxb-your-slack-bot-token"
```

### With JIRA Integration

```bash
python runner.py \
  --channel "#incident-channel" \
  --bedrock-model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
  --slack-token "xoxb-your-slack-bot-token" \
  --jira-user "your-email@company.com" \
  --jira-token "your-jira-api-token" \
  --jira-server "https://yourcompany.atlassian.net"
```

### Command Line Arguments

- `--channel` (required): Slack channel name or ID (e.g., "#incident-channel")
- `--bedrock-model-id` (required): AWS Bedrock model ID
- `--slack-token` (required): Slack Bot Token (starts with "xoxb-")
- `--jira-user` (optional): JIRA username/email for authentication
- `--jira-token` (optional): JIRA API token
- `--jira-server` (optional): JIRA server URL

## Configuration

### Slack Setup

1. Create a Slack App at https://api.slack.com/apps
2. Add the following OAuth scopes:
   - `channels:history`
   - `channels:read`
   - `files:read`
   - `groups:history`
   - `groups:read`
   - `im:history`
   - `im:read`
   - `mpim:history`
   - `mpim:read`
3. Install the app to your workspace
4. Copy the Bot User OAuth Token

### JIRA Setup (Optional)

1. Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Use your JIRA email and the API token for authentication

### AWS Bedrock Setup

1. Ensure your AWS account has access to Bedrock
2. Request access to the desired model (e.g., Claude 3 Sonnet)
3. Configure AWS credentials using `aws configure` or environment variables

## Output Format

The tool generates structured Markdown reports with three main sections:

### 1. Root Cause Analysis (RCA)
- Detailed technical analysis of issues
- Contributing factors and cascading effects
- Missing safeguards and context

### 2. Developer Learnings / Improvements / Action Items
- Actionable technical improvements
- Numbered list of specific action items

### 3. QA Learnings / Improvements / Action Items
- QA-specific learnings and improvements
- Concrete action items for testing processes

## Technical Details

### Message Processing

- Fetches messages in batches of 200
- Processes threads recursively
- Downloads and includes file attachments
- Filters out system messages (joins/leaves)
- Removes user mentions for cleaner analysis

### AI Analysis

- Chunks messages into manageable sizes (300K characters by default)
- Applies multi-level summarization for large datasets
- Uses specialized prompts for technical analysis
- Handles context length limitations through hierarchical reduction

### Error Handling

- Graceful handling of archived channels
- Timeout protection for file downloads
- Retry logic for API failures
- Comprehensive logging throughout the process

## Dependencies

- `slack-sdk`: Slack API client
- `langchain-aws`: AWS Bedrock integration
- `langchain-core`: Core LangChain functionality
- `boto3`: AWS SDK
- `jira`: JIRA API client
- `requests`: HTTP client for file downloads

## Limitations

- Requires appropriate Slack permissions
- AWS Bedrock model access and costs apply
- File download timeouts may occur for large files
- Archived channels are automatically skipped

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

