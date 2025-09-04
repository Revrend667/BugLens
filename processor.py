import logging
from models import BedrockOutput

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    def process(self, bedrock_response: dict):
        try:
            output = BedrockOutput(**bedrock_response)
            valid_items = [ai for ai in output.action_items if ai.confidence >= self.threshold]
            return output.summary, valid_items, output.categories
        except Exception as e:
            logger.error(f"Processor error: {e}")
            return None, [], []
