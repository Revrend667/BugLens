# Slack Channel Analyzer

A Python tool that analyzes Slack channel conversations using AWS Bedrock AI to generate detailed Root Cause Analysis (RCA) reports and actionable learnings for development and QA teams.

## Features

- **Comprehensive Message Processing**: Fetches all messages, threads, attachments, and file contents from Slack channels
- **JIRA Integration**: Automatically expands JIRA ticket references with full issue details
- **AI-Powered Analysis**: Uses AWS Bedrock (Claude) to generate structured RCA reports
- **Chunked Processing**: Handles large conversations by intelligently chunking content
- **Multi-level Summarization**: Merges partial analyses into unified, deduplicated reports

## Architecture

The tool consists of several key components:

- **`SlackScanner`**: Fetches and processes Slack messages, threads, and attachments
- **`JiraClient`**: Integrates with JIRA to fetch ticket details
- **`BedrockClient`**: Handles AI analysis using AWS Bedrock
- **`SlackProcessor`**: Orchestrates the entire analysis workflow
- **`runner.py`**: Command-line interface for the tool

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd slack-channel-analyzer
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
  --channel "C1234567890" \
  --bedrock-model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
  --slack-token "xoxb-your-slack-bot-token"
```

### With JIRA Integration

```bash
python runner.py \
  --channel "C1234567890" \
  --bedrock-model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
  --slack-token "xoxb-your-slack-bot-token" \
  --jira-user "your-email@company.com" \
  --jira-token "your-jira-api-token" \
  --jira-server "https://yourcompany.atlassian.net"
```

## Configuration

### Required Parameters

- `--channel`: Slack channel ID (found in channel URL)
- `--bedrock-model-id`: AWS Bedrock model ID (e.g., `anthropic.claude-3-sonnet-20240229-v1:0`)
- `--slack-token`: Slack Bot Token with appropriate permissions

### Optional Parameters

- `--jira-user`: JIRA username/email for ticket expansion
- `--jira-token`: JIRA API token
- `--jira-server`: JIRA server URL

## Slack Bot Setup

1. Create a Slack app at [api.slack.com](https://api.slack.com/apps)
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

## Output Format

The tool generates structured analysis reports in the following format:

```markdown
### 1. Root Cause Analysis (RCA)
- Detailed technical analysis of issues and their causes
- Contributing factors and cascading effects
- Missing safeguards and context

### 2. Developer Learnings / Improvements / Action Items
- Actionable technical improvements
- Numbered list of specific recommendations

### 3. QA Learnings / Improvements / Action Items
- QA-specific learnings and recommendations
- Testing and validation improvements
```

## Technical Details

### Message Processing

- Fetches messages using Slack's conversations API with pagination
- Processes threaded conversations recursively
- Downloads and includes file attachments
- Expands JIRA ticket references with full details
- Filters out system messages (joins/leaves)

### AI Analysis

- Uses chunked processing for large conversations (300K character chunks)
- Implements multi-level summarization for very large datasets
- Applies deduplication to eliminate redundant insights
- Focuses on high-signal technical analysis

### Error Handling

- Graceful handling of API failures
- Comprehensive logging throughout the process
- Fallback mechanisms for partial failures

## Dependencies

- `slack-sdk`: Slack API integration
- `langchain-aws`: AWS Bedrock integration
- `boto3`: AWS SDK
- `jira`: JIRA API integration
- `requests`: HTTP requests for file downloads

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

