from typing import List
from jwrag.models import SynthesisOption, SynthesisResult


class TUIRenderer:
     """Formats and renders SynthesisResult for terminal output."""
    
    def render_query(self, query: str) -> str:
         return f"\n--- Query ---\n{query}\n"

    def render_options(self, options: List[SynthesisOption]) -> str:
         if not options:
             return "No judgment options generated.\n"
         output = "\n--- Options ---\n"
         for i, opt in enumerate(options, 1):
             output += f"[{i}] {opt.title}\nReasoning: {opt.reasoning}\nConclusions: {', '.join(opt.conclusions)}\n\n"
         return output

    def render_references(self, references: List[str]) -> str:
         if not references:
             return ""
         output = "\n--- References ---\n"
         for ref in references:
             output += f"- {ref}\n"
         return output

    def render_result(self, result: SynthesisResult) -> str:
         out = self.render_query(result.query)
         out += self.render_options(result.options)
         out += self.render_references(result.references)
         return out
