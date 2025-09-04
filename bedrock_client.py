from typing import List
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage
from logger import logger


class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-west-2", chunk_size: int = 50000, max_context_chars: int = 200000):
        """
        Initialize Bedrock Chat client.
        :param model_id: Bedrock model ID (Claude, etc.)
        :param region_name: AWS region
        :param chunk_size: Max characters per chunk
        :param max_context_chars: Maximum safe context length for reduce step
        """
        self.client = ChatBedrock(model_id=model_id, region_name=region_name)
        self.chunk_size = chunk_size
        self.max_context_chars = max_context_chars

    def _chunk_messages(self, messages: List[str]) -> List[str]:
        """
        Break messages into character-bounded chunks.
        """
        chunks = []
        current_chunk = ""
        for msg in messages:
            if len(current_chunk) + len(msg) + 2 > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = msg
            else:
                current_chunk += ("\n\n" if current_chunk else "") + msg
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _analyze_chunk(self, chunk: str, idx: int, total: int) -> str:
        """
        Summarize a single chunk with a strong, detailed RCA/QA prompt.
        """
        prompt = (
            "You are a world-class Staff SDET specializing in distributed systems, "
            "database internals, and infrastructure reliability. "
            "Analyze the following Slack thread chunk and produce a **detailed, structured analysis**.\n\n"
            f"Chunk {idx}/{total}:\n{chunk}\n\n"
            "Return output in the following Markdown structure:\n\n"
            "### 1. Root Cause Analysis (RCA)\n"
            "- Explain the precise technical causes, contributing factors, cascading effects, and context.\n"
            "- Be specific and avoid vague statements.\n\n"
            "### 2. Developer Learnings / Improvements / Action Items\n"
            "- Provide actionable, technical improvements (design, code, monitoring, resilience).\n"
            "- Use a numbered Markdown list.\n\n"
            "### 3. QA Learnings / Improvements / Action Items\n"
            "- Provide concrete QA learnings (test gaps, automation, chaos testing, CI/CD, monitoring).\n"
            "- Use a numbered Markdown list.\n\n"
            "⚠️ Important Instructions:\n"
            "- Do not repeat points in different words.\n"
            "- Output must be detailed but **crisp and high-signal only**.\n"
            "- Do not summarize the Slack messages — only return analysis."
        )
        try:
            response = self.client.invoke([HumanMessage(content=prompt)])
            return getattr(response, "content", "").strip()
        except Exception as e:
            logger.error(f"Bedrock chunk analysis failed (chunk {idx}/{total}): {e}")
            return ""

    def _merge_summaries(self, summaries: List[str]) -> str:
        """
        Merge multiple intermediate summaries into a final deduplicated RCA/QA report.
        Uses multi-level reduce if summaries are too long.
        """
        if not summaries:
            return ""

        # Multi-level reduce: process in batches if combined size exceeds limit
        while sum(len(s) for s in summaries) > self.max_context_chars and len(summaries) > 1:
            logger.info("Intermediate summaries too large, applying multi-level reduce...")
            new_summaries = []
            for i in range(0, len(summaries), 3):  # batch reduce in groups of 3
                batch = summaries[i:i + 3]
                prompt = (
                    "You are a world-class Staff SDET. Merge the following partial analyses "
                    "into a single, **deduplicated** report:\n\n"
                    f"{chr(10).join(batch)}\n\n"
                    "Return output in this exact structure:\n"
                    "### 1. Root Cause Analysis (RCA)\n"
                    "### 2. Developer Learnings / Improvements / Action Items\n"
                    "### 3. QA Learnings / Improvements / Action Items\n\n"
                    "⚠️ Instructions: Eliminate redundancy, do not rephrase the same points, "
                    "and keep only unique, high-signal insights."
                )
                try:
                    response = self.client.invoke([HumanMessage(content=prompt)])
                    merged = getattr(response, "content", "").strip()
                    if merged:
                        new_summaries.append(merged)
                except Exception as e:
                    logger.error(f"Bedrock batch reduce failed: {e}")
            summaries = new_summaries or summaries  # fallback to old if failed

        # Final reduce
        combined_prompt = (
            "You are a world-class Staff SDET specializing in distributed systems, "
            "database internals, and infrastructure reliability. "
            "The following are **partial analyses** from multiple chunks of a Slack thread. "
            "Your job is to produce a **final, unified, deduplicated report**.\n\n"
            "Partial Summaries:\n"
            f"{chr(10).join(summaries)}\n\n"
            "Final output must strictly follow this Markdown structure:\n\n"
            "### 1. Root Cause Analysis (RCA)\n"
            "- Single, unified RCA covering all chunks.\n"
            "- Include root causes, contributing factors, cascading failures, and missing safeguards.\n\n"
            "### 2. Developer Learnings / Improvements / Action Items\n"
            "- Deduplicated list of actionable developer improvements.\n"
            "- Remove repeated or rephrased items.\n"
            "- Use a numbered Markdown list.\n\n"
            "### 3. QA Learnings / Improvements / Action Items\n"
            "- Deduplicated list of QA-specific improvements.\n"
            "- Remove repeated or rephrased items.\n"
            "- Use a numbered Markdown list.\n\n"
            "⚠️ Important:\n"
            "- Eliminate redundancy across chunks.\n"
            "- Do not restate Slack text.\n"
            "- Keep output detailed but crisp."
        )
        try:
            response = self.client.invoke([HumanMessage(content=combined_prompt)])
            return getattr(response, "content", "").strip()
        except Exception as e:
            logger.error(f"Bedrock final reduce failed: {e}")
            return "\n".join(summaries)

    def summarize(self, messages: List[str]) -> str:
        """
        Main entry: Summarize messages into final RCA/QA learnings.
        """
        try:
            chunks = self._chunk_messages(messages)
            logger.info("Processing %s chunks...", len(chunks))

            intermediate_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info("Analyzing chunk %s/%s", i + 1, len(chunks))
                summary = self._analyze_chunk(chunk, i + 1, len(chunks))
                if summary:
                    intermediate_summaries.append(summary)

            if not intermediate_summaries:
                logger.warning("No intermediate summaries generated.")
                return ""

            final_summary = self._merge_summaries(intermediate_summaries)
            if not final_summary:
                logger.warning("Final Bedrock summary is empty")
            return final_summary

        except Exception as e:
            logger.error(f"Bedrock RCA generation failed: {e}")
            return ""
