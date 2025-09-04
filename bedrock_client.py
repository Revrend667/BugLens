from typing import List

from langchain.schema import HumanMessage
from langchain_aws import ChatBedrock

from logger import logger


class BedrockClient:
    def __init__(
        self,
        model_id: str,
        region_name: str = "us-west-2",
        chunk_size: int = 300_000,
        max_chars: int = 5_000_000,
    ):
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

        logger.info(
            f"Reduced to {len(kept_chunks)} chunks, total length {running_total}"
        )
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
                    "You are a world-class Staff SDET specializing in distributed systems, "
                    "database internals, and large-scale infrastructure testing. Your task is to "
                    "analyze the following Slack thread chunk and produce a highly detailed and "
                    "technical Root Cause Analysis (RCA), followed by concrete learnings and "
                    "action items for both Development and QA teams.\n\n"
                    f"Chunk {i+1}/{len(chunks)}:\n{chunk}\n\n"
                    "Your response must follow this **exact structure** in Markdown:\n\n"
                    "### 1. Root Cause Analysis (RCA)\n"
                    "- Explain the precise technical cause(s) of the issue.\n"
                    "- Include contributing factors, cascading effects, and environmental conditions.\n"
                    "- Reference evidence from the Slack thread to support the RCA.\n"
                    "- Highlight why existing safeguards failed (if applicable).\n\n"
                    "### 2. Developer Learnings / Improvements / Action Items\n"
                    "- Identify gaps in design, implementation, or architecture.\n"
                    "- Propose concrete fixes (e.g., better error handling, retries, schema changes, "
                    "resource isolation, feature flags).\n"
                    "- Suggest long-term preventive measures (e.g., design reviews, better API contracts, "
                    "monitoring metrics, alert thresholds).\n"
                    "- Output as a numbered or bulleted list with actionable, technical steps.\n\n"
                    "### 3. QA Learnings / Improvements / Action Items\n"
                    "- Identify missed test cases, blind spots in automation, and gaps in validation.\n"
                    "- Propose test strategy improvements (e.g., chaos testing, failure injection, regression "
                    "coverage, boundary testing).\n"
                    "- Suggest CI/CD and observability enhancements (e.g., log analysis, anomaly detection, "
                    "alerting improvements).\n"
                    "- Output as a numbered or bulleted list with actionable, technical steps.\n\n"
                    "⚠️ Important Instructions:\n"
                    "- Be **technical, specific, and detailed** — avoid generic advice.\n"
                    "- Use Markdown formatting so the output is structured and easy to parse.\n"
                    "- Do **not** repeat the Slack messages — only return your expert analysis."
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
