# agent-skill-gen

Auto-generate structured skill files from agent conversation logs. Inspired by MemOS and Hermes Agent (July 2026) — the "memory that evolves" frontier.

Extracts tool sequences, error recoveries, and repeated tasks from agent traces. Generates Markdown skill files ready for Claude Code, Codex, or Hermes.

```bash
pip install agent-skill-gen
agent-skill-gen generate traces.jsonl --output skills/
agent-skill-gen analyze traces.jsonl
```

MIT
