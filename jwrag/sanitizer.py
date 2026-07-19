from presidio_analyzer import AnalyzerEngine
import re

class DataSanitizer:
    def __init__(self) -> None:
        self.analyzer = AnalyzerEngine()

    def anonymize(self, text: str) -> tuple[str, dict[str, str]]:
        # Analyze the text for PII
        results = self.analyzer.analyze(text=text, language='en')
        
        # Sort by start (asc), then end (desc) to keep the longest spanning entities
        results = sorted(results, key=lambda x: (x.start, -x.end))
        
        filtered = []
        last_end = -1
        for result in results:
            if result.start >= last_end:
                filtered.append(result)
                last_end = result.end
                
        # Sort filtered results by start index in descending order
        # so replacing text doesn't shift the indices for previous entities
        filtered = sorted(filtered, key=lambda x: x.start, reverse=True)
        
        mapping = {}
        type_counters: dict[str, int] = {}
        
        anon_text = text
        for result in filtered:
            entity_type = result.entity_type
            
            # Increment counter for this entity type
            type_counters[entity_type] = type_counters.get(entity_type, 0) + 1
            placeholder = f"<{entity_type}_{type_counters[entity_type]}>"
            
            # Extract the original text
            original_value = anon_text[result.start:result.end]
            
            # Save to mapping
            mapping[placeholder] = original_value
            
            # Replace in text
            anon_text = anon_text[:result.start] + placeholder + anon_text[result.end:]
            
        return anon_text, mapping

    def deanonymize(self, text: str, mapping: dict[str, str]) -> str:
        # Simple string replacement for all placeholders
        # Sort keys by length descending to avoid partial replacements if there are overlapping prefixes
        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
        
        restored_text = text
        for placeholder in sorted_keys:
            restored_text = restored_text.replace(placeholder, mapping[placeholder])
            
        return restored_text
