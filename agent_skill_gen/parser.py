"""Parse agent conversation traces."""

import json
from agent_skill_gen.types import TraceEntry


def parse_traces(path: str) -> list[TraceEntry]:
    entries: list[TraceEntry] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            obj = json.loads(line)
            entries.append(TraceEntry(role=obj.get("role","unknown"), content=obj.get("content",""), tool_calls=obj.get("tool_calls",obj.get("tools",[])), timestamp=obj.get("timestamp","")))
    return entries


def parse_traces_json(path: str) -> list[TraceEntry]:
    with open(path, encoding="utf-8") as f: data = json.load(f)
    if isinstance(data, list): return [TraceEntry(role=e.get("role","unknown"), content=e.get("content",""), tool_calls=e.get("tool_calls",e.get("tools",[])), timestamp=e.get("timestamp","")) for e in data]
    return []
