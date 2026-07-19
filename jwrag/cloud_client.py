import json
import re
from typing import List, Optional
import numpy as np
from loguru import logger
from openai import OpenAI

from jwrag.interfaces import ISynthesisEngine
from jwrag.models import Chunk, SynthesisOption, SynthesisResult
from jwrag.sanitizer import DataSanitizer


class CloudSynthesisEngine(ISynthesisEngine):
    """Handles embedding generation and LLM-based synthesis via Cloud API with local data sanitization."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", 
                 embedding_model: str = "text-embedding-3-small", 
                 synthesis_model: str = "gpt-4o") -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.embedding_model = embedding_model
        self.synthesis_model = synthesis_model
        self.sanitizer = DataSanitizer()

    def generate_embedding(self, text: str) -> np.ndarray:
        """Sanitizes text and generates an embedding vector using the Cloud API."""
        anon_text, _ = self.sanitizer.anonymize(text)
        
        try:
            response = self.client.embeddings.create(
                input=anon_text,
                model=self.embedding_model
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Cloud embedding request failed: {e}")
            raise

    def synthesize(self, query: str, chunks: List[Chunk]) -> SynthesisResult:
        """Constructs prompt, sanitizes, requests LLM synthesis, and parses/de-anonymizes the result."""
        
        # Combine text content from chunks
        context_text = "\n\n---\n\n".join([chunk.text_content for chunk in chunks])
        
        # Anonymize context and query
        anon_context, context_mapping = self.sanitizer.anonymize(context_text)
        anon_query, query_mapping = self.sanitizer.anonymize(query)
        
        # Merge mappings (assuming minimal conflicts for now)
        mapping = {**context_mapping, **query_mapping}
        
        prompt = f"""You are JWRAG (Judgement Weighted RAG), a multi-perspective decision-support engine. 
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
{anon_context}
---
USER QUERY:
{anon_query}
"""
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.synthesis_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} if "gpt" in self.synthesis_model else None
                )
                
                raw_response = response.choices[0].message.content or ""
                
                parsed_data = self._parse_json(raw_response)
                if parsed_data and "options" in parsed_data:
                    return self._build_synthesis_result(query, parsed_data["options"], mapping)
                    
                logger.warning(f"Attempt {attempt + 1}: Failed to extract valid JSON options. Retrying...")
                
            except Exception as e:
                logger.error(f"Cloud synthesis attempt {attempt + 1} failed: {e}")
                
        # Hard Fallback
        logger.error("Exhausted all retries for LLM synthesis. Returning hard fallback.")
        return SynthesisResult(
            query=query,
            options=[SynthesisOption(title="Parsing Failure", reasoning="The model failed to generate valid structured output.", conclusions=[])],
            references=[]
        )

    def _parse_json(self, raw_text: str) -> Optional[dict]:
        """Implements the robust multi-stage JSON parsing pipeline."""
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass
            
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
            
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
                
        return None

    def _build_synthesis_result(self, original_query: str, options_data: list, mapping: dict[str, str]) -> SynthesisResult:
        """Maps parsed JSON data to SynthesisResult DTO and de-anonymizes fields."""
        synthesis_options = []
        for opt in options_data:
            title = self.sanitizer.deanonymize(opt.get("title", "Untitled"), mapping)
            reasoning = self.sanitizer.deanonymize(opt.get("reasoning", ""), mapping)
            conclusions = [self.sanitizer.deanonymize(c, mapping) for c in opt.get("conclusions", [])]
            
            synthesis_options.append(SynthesisOption(
                title=title,
                reasoning=reasoning,
                conclusions=conclusions
            ))
        return SynthesisResult(query=original_query, options=synthesis_options, references=[])
