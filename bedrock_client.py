from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage
from logger import logger

class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-west-2"):
        # Initialize Bedrock Chat client
        self.client = ChatBedrock(model_id=model_id, region_name=region_name)

    def summarize(self, prompt: str) -> str:
        """
        Sends the prompt to Bedrock and returns the raw output.
        """
        try:
            # Use invoke instead of deprecated predict_messages
            response = self.client.invoke([HumanMessage(content=prompt)])
            
            # Extract the content
            text_output = getattr(response, "content", "")
            if not text_output:
                logger.warning("Bedrock returned empty response")
            return text_output

        except Exception as e:
            logger.error(f"Bedrock summarize failed: {e}")
            return ""
