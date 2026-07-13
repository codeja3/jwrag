import json
import re
from typing import List, Optional
import numpy as np
import httpx
from loguru import logger
from jwrag.interfaces import ISynthesisEngine
from jwrag.models import Chunk, SynthesisOption, SynthesisResult


class OllamaSynthesisEngine(ISynthesisEngine):
     """Handles embedding generation and LLM-based synthesis via local Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", 
                 embedding_model: str = "qwen3-embedding:4b", 
                 synthesis_model: str = "gemma4:26b-mlx") -> None:
        self.base_url = base_url.rstrip("/")
        self.embedding_model = embedding_model
        self.synthesis_model = synthesis_model
        self.client = httpx.Client(timeout=120.0)

    def generate_embedding(self, text: str) -> np.ndarray:
         """Generates an embedding vector for the given text using Ollama's API."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text}
             )
            response.raise_for_status()
            data = response.json()
            return np.array(data["embedding"], dtype=np.float32)
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama embedding request failed with status {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise

    def synthesize(self, query: str, chunks: List[Chunk]) -> SynthesisResult:
         """Constructs prompt, requests LLM synthesis from Ollama, and parses the multi-perspective result."""
        context_text = "\n\n---\n\n".join([chunk.text_content for chunk in chunks])
        
        prompt = f"""You are JWRAG (Judgement Weighted RAG), a local multi-perspective decision-support engine. 
Analyze the provided document context below to answer the user's query.

INSTRUCTIONS:
1. Provide at least two distinct, non-identical judgment options or perspectives (e.g. Option A: Conservative, Option B: Progressive).
2. For each option, specify:
     - A descriptive Title.
     - Detailed Reasoning based on the text.
     - Key Conclusions or actions.
3. Reference ONLY the provided context. If the context does not contain enough information, explain that.
4. Format your output strictly in JSON according to this structure:
{{
    "options": [
      {{
        "title": "Option Title",
        "reasoning": "Detailed justification...",
        "conclusions": ["Conclusion 1", "Conclusion 2"]
      }}
    ]
}}

---
CONTEXT:
{context_text}
---
USER QUERY:
{query}
"""
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = self.client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.synthesis_model, "prompt": prompt, "stream": False}
                 )
                response.raise_for_status()
                raw_response = response.json().get("response", "")
                
                parsed_data = self._parse_json(raw_response)
                if parsed_data and "options" in parsed_data:
                    return self._build_synthesis_result(query, parsed_data["options"])
                    
                logger.warning(f"Attempt {attempt + 1}: Failed to extract valid JSON options. Retrying...")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama synthesis request failed with status {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Synthesis attempt {attempt + 1} failed: {e}")
                
        # Hard Fallback
        logger.error("Exhausted all retries for LLM synthesis. Returning hard fallback.")
        return SynthesisResult(
            query=query,
            options=[SynthesisOption(title="Parsing Failure", reasoning="The model failed to generate valid structured output. Please try again or check logs.", conclusions=[])],
            references=[]
         )

    def _parse_json(self, raw_text: str) -> Optional[dict]:
         """Implements the robust multi-stage JSON parsing pipeline."""
        # 1. Direct Parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass
            
        # 2. Markdown Fence Stripping
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
            
        # 3. Regex Extraction
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
                
        return None

    def _build_synthesis_result(self, query: str, options_data: list) -> SynthesisResult:
         """Maps parsed JSON data to SynthesisResult DTO."""
        synthesis_options = []
        for opt in options_data:
            synthesis_options.append(SynthesisOption(
                title=opt.get("title", "Untitled"),
                reasoning=opt.get("reasoning", ""),
                conclusions=opt.get("conclusions", [])
             ))
        return SynthesisResult(query=query, options=synthesis_options, references=[])
