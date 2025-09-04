from langchain_aws import ChatBedrock
from logger import logger

class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-west-2"):
        self.client = ChatBedrock(model_id=model_id, region_name=region_name)

    def summarize(self, prompt: str) -> str:
        """
        Returns whatever Bedrock outputs. No parsing.
        """
        response = self.client.predict_messages(messages=[{"role": "user", "content": prompt}])
        text_output = response.message.content[0].text if response.message.content else ""
        if not text_output:
            logger.warning("Bedrock returned empty response")
        return text_output
