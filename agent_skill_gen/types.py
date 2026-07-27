"""Core types for skill generation."""

from dataclasses import dataclass, field


@dataclass
class TraceEntry:
    role: str
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class SkillTemplate:
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source_pattern: str = ""

    def to_markdown(self) -> str:
        lines = [f"# Skill: {self.name}", "", f"**Confidence:** {self.confidence:.0%}", "", f"## Description\n{self.description}\n"]
        if self.triggers:
            lines.append("## Triggers\n")
            for t in self.triggers: lines.append(f"- {t}")
            lines.append("")
        if self.steps:
            lines.append("## Steps\n")
            for i, s in enumerate(self.steps, 1): lines.append(f"{i}. {s}")
            lines.append("")
        if self.examples:
            lines.append("## Examples\n")
            for e in self.examples: lines.append(f"- {e}")
            lines.append("")
        return "\n".join(lines)


@dataclass
class SkillReport:
    total_traces: int
    patterns_found: int
    skills_generated: int
    skills: list[SkillTemplate]
    summary: str = ""

    def to_dict(self) -> dict:
        return {"total_traces": self.total_traces, "patterns_found": self.patterns_found, "skills_generated": self.skills_generated, "skills": [{"name": s.name, "confidence": s.confidence, "pattern": s.source_pattern} for s in self.skills]}
