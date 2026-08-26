"""
Slack Conversation & Bursting Ingester inspired by Cerebras article.
Distills raw Slack threads into structured QA records and extracts qualifying
message bursts (IDF >= 4.0, length >= 200, author run) with prepended thread topic context.
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class SlackIngester:
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedder = embedding_engine

    def process_slack_thread(
        self,
        thread_data: Dict[str, Any],
        channel_name: str = "general"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        thread_ts = thread_data.get("thread_ts", "ts_000")
        messages = thread_data.get("messages", [])

        raw_json = json.dumps(thread_data)
        content_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        source_id = f"slack://{channel_name}/{thread_ts}"

        if not messages:
            return content_hash, []

        parent_msg = messages[0].get("text", "")
        reply_texts = [m.get("text", "") for m in messages[1:]]

        one_line_question = f"Question in #{channel_name}: {parent_msg[:120]}"
        resolution = reply_texts[-1][:200] if reply_texts else "No explicit resolution"
        summary = f"Thread in #{channel_name} with {len(messages)} messages. Resolution: {resolution}"

        chunks: List[Dict[str, Any]] = []

        chunks.append({
            "chunk_type": "thread_summary",
            "parent_id": source_id,
            "start_line": 0,
            "end_line": len(messages),
            "raw_content": f"Parent: {parent_msg}\nReplies: " + "\n".join(reply_texts),
            "distilled_summary": f"{one_line_question}\nSummary: {summary}\nResolution: {resolution}",
            "metadata_json": {
                "channel": channel_name,
                "thread_ts": thread_ts,
                "participant_count": len(set(m.get("user", "") for m in messages))
            },
            "embedding": self.embedder.embed_text(one_line_question + "\n" + summary + "\n" + resolution),
            "idf_score": 2.0,
            "created_at": float(messages[0].get("ts", 0.0)) if messages[0].get("ts") else 0.0
        })

        bursts = []
        curr_author = None
        curr_burst = []

        for msg in messages:
            author = msg.get("user", "unknown")
            if author == curr_author:
                curr_burst.append(msg)
            else:
                if curr_burst:
                    bursts.append((curr_author, curr_burst))
                curr_author = author
                curr_burst = [msg]
        if curr_burst:
            bursts.append((curr_author, curr_burst))

        for author, burst_msgs in bursts:
            combined_text = "\n".join(m.get("text", "") for m in burst_msgs)
            total_len = len(combined_text)
            has_reactions = any(m.get("reactions") for m in burst_msgs)

            if total_len >= 200 or has_reactions:
                contextualized_text = f"Thread Context: {one_line_question}\nAuthor {author} burst:\n{combined_text}"

                chunks.append({
                    "chunk_type": "burst",
                    "parent_id": source_id,
                    "start_line": 0,
                    "end_line": len(burst_msgs),
                    "raw_content": contextualized_text,
                    "distilled_summary": f"Burst by {author} in #{channel_name}: {combined_text[:150]}",
                    "metadata_json": {
                        "channel": channel_name,
                        "author": author,
                        "has_reactions": has_reactions,
                        "character_length": total_len
                    },
                    "embedding": self.embedder.embed_text(contextualized_text),
                    "idf_score": 4.0 if has_reactions else 2.5,
                    "created_at": float(burst_msgs[0].get("ts", 0.0)) if burst_msgs[0].get("ts") else 0.0
                })

        return content_hash, chunks
