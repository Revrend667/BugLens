import logging

from jira import JIRA

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, server: str, user: str, token: str):
        if not server or not user or not token:
            self.jira = None
            return
        options = {"server": server}
        try:
            self.jira = JIRA(options=options, basic_auth=(user, token))
        except Exception as e:
            logger.error(f"JIRA init failed: {e}")
            self.jira = None

    def fetch_issue(self, issue_key: str) -> str:
        if not self.jira:
            return ""
        try:
            issue = self.jira.issue(issue_key)
            return f"Summary: {issue.fields.summary}\nDescription: {issue.fields.description}"
        except Exception as e:
            logger.warning(f"Failed to fetch JIRA issue {issue_key}: {e}")
            return ""
