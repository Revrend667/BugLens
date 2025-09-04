from typing import List

class Preprocessor:
    def prepare_prompt_payload(self, messages: List[str]) -> str:
        """
        Simply join all messages into a single prompt for Bedrock.
        We let the model handle summarization, RCA, QA learnings.
        """
        return "\n\n".join(messages)
