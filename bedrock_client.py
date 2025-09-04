from typing import List
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage
from logger import logger

class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-west-2"):
        """
        Initialize Bedrock Chat client.
        """
        self.client = ChatBedrock(model_id=model_id, region_name=region_name)

    def get_rca(self, messages: List[str]) -> str:
        """
        Sends Slack messages to Bedrock and requests a detailed RCA & QA learnings.
        """
        # Combine messages into one prompt
        prompt = (
            "You are a world class Staff SDET. Read the following Slack thread and produce:\n"
            "1. Detailed RCA (Root Cause Analysis) of the issue.\n"
            "2. Key Developer learnings / improvements for the Dev team.\n"
            "23. Key QA learnings / improvements for the QA team.\n\n"
            "Slack messages:\n\n"
        )
        prompt += "\n\n".join(messages)

        try:
            # Send to Bedrock
            response = self.client.invoke([HumanMessage(content=prompt)])

            # Extract content
            text_output = getattr(response, "content", "")
            if not text_output:
                logger.warning("Bedrock returned empty response")
            return text_output

        except Exception as e:
            logger.error(f"Bedrock RCA generation failed: {e}")
            return ""
