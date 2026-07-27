"""Pattern extraction from agent traces."""

import re
from collections import Counter
from agent_skill_gen.types import TraceEntry, SkillTemplate


def extract_tool_sequences(entries: list[TraceEntry], min_length: int = 3) -> list[tuple[str, ...]]:
    sequences: list[tuple[str, ...]] = []; current: list[str] = []
    for e in entries:
        if e.role == "assistant" and e.tool_calls: current.extend(tc.get("name","unknown") for tc in e.tool_calls)
        elif e.role == "user":
            if len(current) >= min_length: sequences.append(tuple(current))
            current = []
    if len(current) >= min_length: sequences.append(tuple(current))
    return sequences


def extract_error_recoveries(entries: list[TraceEntry]) -> list[dict]:
    recoveries: list[dict] = []; i = 0
    while i < len(entries):
        e = entries[i]
        if e.role == "tool" and _is_error(e.content):
            error_msg = e.content[:100]; recovery_steps: list[str] = []
            for j in range(i + 1, min(i + 5, len(entries))):
                next_e = entries[j]
                if next_e.role == "assistant" and next_e.tool_calls: recovery_steps.extend(tc.get("name","") for tc in next_e.tool_calls)
                if next_e.role == "tool" and not _is_error(next_e.content): recovery_steps.append(f"retry: {next_e.content[:50]}"); break
            if recovery_steps: recoveries.append({"error":error_msg,"recovery":recovery_steps,"combined":f"On '{error_msg[:60]}...': {' -> '.join(recovery_steps)}"})
            i = j if recovery_steps else i + 1
        else: i += 1
    return recoveries


def extract_repeated_tasks(entries: list[TraceEntry]) -> list[dict]:
    user_msgs = [e.content for e in entries if e.role == "user"]
    if len(user_msgs) < 2: return []
    tasks: list[dict] = []; seen: set[str] = set()
    for i, msg in enumerate(user_msgs):
        key = _normalize(msg)
        if key in seen or len(key) < 10: continue
        similar = [m for j, m in enumerate(user_msgs) if j != i and _similarity(key, _normalize(m)) > 0.6]
        if len(similar) >= 1: seen.add(key); tasks.append({"pattern":msg[:120],"count":len(similar)+1,"normalized":key})
    return tasks


def extract_all(entries: list[TraceEntry]) -> dict:
    return {"tool_sequences":extract_tool_sequences(entries),"error_recoveries":extract_error_recoveries(entries),"repeated_tasks":extract_repeated_tasks(entries)}


def generate_skills(entries: list[TraceEntry]) -> list[SkillTemplate]:
    patterns = extract_all(entries); skills: list[SkillTemplate] = []
    seq_counter = Counter(patterns["tool_sequences"])
    for seq, count in seq_counter.most_common(10):
        if count < 2: continue
        name = " -> ".join(seq[:4])
        skills.append(SkillTemplate(name=name, description=f"Workflow: {name}", triggers=[f"When task requires: {name}"], steps=[f"Execute {t}" for t in seq], examples=[f"Completed {count}x"], confidence=min(0.9, 0.5+count*0.1), source_pattern="tool-sequence"))
    for rec in patterns["error_recoveries"]:
        etype = "timeout" if "timeout" in rec["error"].lower() else "errors"
        skills.append(SkillTemplate(name=f"Recover from {etype}", description=f"Recovery: {rec['error'][:80]}", triggers=[f"When: {rec['error'][:60]}..."], steps=rec["recovery"], examples=[rec["combined"]], confidence=0.7, source_pattern="error-recovery"))
    for task in patterns["repeated_tasks"]:
        words = _normalize(task["pattern"]).split()[:4]
        skills.append(SkillTemplate(name=f"Handle {' '.join(words)}", description=f"Repeated ({task['count']}x): {task['pattern'][:100]}", triggers=[f"When user asks: {task['pattern'][:80]}"], steps=["Follow the established pattern"], examples=[task["pattern"][:100]], confidence=min(0.85,0.4+task["count"]*0.15), source_pattern="repeated-task"))
    seen = set(); deduped = []
    for s in sorted(skills, key=lambda s: s.confidence, reverse=True):
        if s.name not in seen: seen.add(s.name); deduped.append(s)
    return deduped


def _is_error(content: str) -> bool: return bool(re.search(r'\b(error|fail|exception|timeout|denied|refused|invalid|cannot)\b', content, re.IGNORECASE))
def _normalize(text: str) -> str: return re.sub(r'[^a-z0-9\s]', '', text.lower().strip())
def _similarity(a: str, b: str) -> float:
    a_set, b_set = set(a.split()), set(b.split())
    return len(a_set & b_set) / len(a_set | b_set) if (a_set and b_set) else 0.0
