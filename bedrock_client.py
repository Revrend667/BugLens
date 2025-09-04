import requests
import logging

logger = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key

    def extract(self, messages: list):
        prompt = self._build_prompt(messages)
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'prompt': prompt,
            'max_tokens': 1024,
            'response_format': 'json'
        }
        try:
            r = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Bedrock call failed: {e}")
            return {}

    def _build_prompt(self, messages: list) -> str:
        msg_texts = [f"{m.get('user')}: {m.get('text')}" for m in messages]
        return ("System: Extract QA learnings and action items from the following Slack messages. "
                "Respond in JSON schema format.\nMessages:\n" + "\n".join(msg_texts))