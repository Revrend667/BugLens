from typing import List
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage
from logger import logger


class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-west-2",
                 chunk_size: int = 500_000, max_chars: int = 5_000_000):
        """
        Initialize Bedrock Chat client.
        :param chunk_size: Approximate number of characters per chunk for summarization.
        :param max_chars: Maximum number of characters allowed across all chunks (hard cap).
        """
        self.client = ChatBedrock(model_id=model_id, region_name=region_name)
        self.chunk_size = chunk_size
        self.max_chars = max_chars

    def _chunk_messages(self, messages: List[str]) -> List[str]:
        """
        Break messages into chunks that fit within chunk_size.
        """
        chunks = []
        current_chunk = ""
        for msg in messages:
            if len(current_chunk) + len(msg) + 2 > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = msg
            else:
                current_chunk = f"{current_chunk}\n\n{msg}" if current_chunk else msg
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _enforce_global_limit_on_chunks(self, chunks: List[str]) -> List[str]:
        """
        Enforce global max size across chunks.
        If total > max_chars, keep dropping oldest chunks until under limit.
        """
        total_chars = sum(len(c) for c in chunks)
        if total_chars <= self.max_chars:
            return chunks

        logger.warning(
            f"Total input size {total_chars} exceeds {self.max_chars}. "
            f"Keeping latest chunks until within limit."
        )

        # Keep only recent chunks until size <= max_chars
        kept_chunks = []
        running_total = 0
        for chunk in reversed(chunks):  # start from newest
            chunk_len = len(chunk)
            if running_total + chunk_len > self.max_chars:
                break
            kept_chunks.insert(0, chunk)  # prepend to maintain chronological order
            running_total += chunk_len

        logger.info(f"Reduced to {len(kept_chunks)} chunks, total length {running_total}")
        return kept_chunks

    def summarize(self, messages: List[str]) -> str:
        """
        Generates detailed RCA and QA learnings from Slack messages using Bedrock.
        Uses chunking + map-reduce style summarization for large threads.
        """
        try:
            chunks = self._chunk_messages(messages)
            chunks = self._enforce_global_limit_on_chunks(chunks)

            intermediate_summaries = []

            # Map: summarize each chunk
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)} (size={len(chunk)})")
                prompt = (
                    "You are a world-class Staff SDET. Analyze the following Slack thread "
                    "chunk and produce a detailed RCA, Key Developer Learnings/Improvements/Action Items, "
                    "and Key QA Learnings/Improvements/Action Items.\n\n"
                    f"Chunk {i+1}/{len(chunks)}:\n{chunk}\n\n"
                    "Return structured output with:\n"
                    "1. Detailed Root Cause Analysis\n"
                    "2. Key Developer Learnings / Improvements / Action Items\n"
                    "3. Key QA Learnings / Improvements / Action Items"
                )
                response = self.client.invoke([HumanMessage(content=prompt)])
                text_output = getattr(response, "content", "").strip()
                if text_output:
                    intermediate_summaries.append(text_output)
                else:
                    logger.warning(f"Empty response for chunk {i+1}")

            # Reduce: merge summaries
            if len(intermediate_summaries) == 1:
                final_summary = intermediate_summaries[0]
            else:
                combined_prompt = (
                    "You are a world-class Staff SDET. The following are summaries of "
                    "different chunks of a Slack thread. Merge them into one comprehensive, "
                    "detailed RCA and QA learnings report.\n\n"
                    "Summaries:\n" + "\n\n".join(intermediate_summaries)
                )
                response = self.client.invoke([HumanMessage(content=combined_prompt)])
                final_summary = getattr(response, "content", "").strip()

            if not final_summary:
                logger.warning("Final summary is empty")
            return final_summary

        except Exception as e:
            logger.error(f"Bedrock RCA generation failed: {e}")
            return ""
