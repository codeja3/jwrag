from typing import List
from jwrag.models import SynthesisOption, SynthesisResult, Reference


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

    def render_references(self, references: List[Reference]) -> str:
        if not references:
            return ""
        output = "\n--- References ---\n"
        order = ["chapter", "section", "clause", "page", "paragraph"]
        for ref in references:
            ref_str = ref.filename
            parts = []
            markers = ref.markers.copy()
            for key in order:
                if key in markers:
                    val = markers.pop(key)
                    if key == "chapter":
                        parts.append(f"Ch. {val}")
                    elif key in ("section", "clause"):
                        parts.append(f"§ {val}")
                    elif key == "page":
                        parts.append(f"p. {val}")
                    elif key == "paragraph":
                        parts.append(f"¶ {val}")
            for key, val in markers.items():
                parts.append(f"{key.capitalize()}: {val}")
            if parts:
                ref_str += f" ({', '.join(parts)})"
            output += f"- {ref_str}\n"
        return output

    def render_result(self, result: SynthesisResult) -> str:
        out = self.render_query(result.query)
        out += self.render_options(result.options)
        out += self.render_references(result.references)
        return out
