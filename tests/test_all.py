import json, os, tempfile, pytest, sys
from agent_skill_gen.types import TraceEntry, SkillTemplate
from agent_skill_gen.parser import parse_traces, parse_traces_json
from agent_skill_gen.extractor import extract_tool_sequences, extract_error_recoveries, extract_repeated_tasks, extract_all, generate_skills


def _jl(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path,"w",encoding="utf-8") as f:
        for o in lines: f.write(json.dumps(o)+"\n")
    return path

def _j(data):
    fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd)
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f)
    return path

def _sample():
    return [{"role":"user","content":"Search Python"},{"role":"assistant","content":"","tool_calls":[{"name":"search","args":{}}]},{"role":"tool","content":"Found"},{"role":"assistant","content":"","tool_calls":[{"name":"sort","args":{}}]},{"role":"tool","content":"Sorted"},{"role":"assistant","content":"","tool_calls":[{"name":"filter","args":{}}]},{"role":"tool","content":"Filtered"},{"role":"user","content":"Search Python"},{"role":"assistant","content":"","tool_calls":[{"name":"search","args":{}}]},{"role":"tool","content":"Found 55"},{"role":"assistant","content":"","tool_calls":[{"name":"sort","args":{}}]},{"role":"tool","content":"Sorted"},{"role":"assistant","content":"","tool_calls":[{"name":"filter","args":{}}]},{"role":"tool","content":"Filtered"}]

def _err():
    return [{"role":"user","content":"Deploy"},{"role":"assistant","content":"","tool_calls":[{"name":"deploy","args":{}}]},{"role":"tool","content":"Error: timeout"},{"role":"assistant","content":"","tool_calls":[{"name":"health_check","args":{}}]},{"role":"tool","content":"healthy"},{"role":"assistant","content":"","tool_calls":[{"name":"deploy","args":{}}]},{"role":"tool","content":"Deployed"}]


class TestParser:
    def test_jsonl(self):
        p = _jl([{"role":"user","content":"hi"}]); e = parse_traces(p); os.unlink(p)
        assert len(e) == 1 and e[0].role == "user"
    def test_json(self):
        p = _j([{"role":"user","content":"hi"}]); e = parse_traces_json(p); os.unlink(p)
        assert len(e) == 1


class TestExtractor:
    def test_tool_seqs(self):
        t = [TraceEntry(**e) for e in _sample()]; s = extract_tool_sequences(t)
        assert len(s) >= 1 and any("search" in x for x in s)
    def test_errors(self):
        t = [TraceEntry(**e) for e in _err()]; r = extract_error_recoveries(t)
        assert len(r) >= 1 and "health_check" in r[0]["recovery"]
    def test_repeated(self):
        t = [TraceEntry(**e) for e in _sample()]; r = extract_repeated_tasks(t)
        assert len(r) >= 1 and any("python" in x["normalized"] for x in r)
    def test_all(self):
        t = [TraceEntry(**e) for e in _sample()+_err()]; p = extract_all(t)
        assert len(p["tool_sequences"]) >= 1 and len(p["error_recoveries"]) >= 1
    def test_skills(self):
        t = [TraceEntry(**e) for e in _sample()+_err()]; s = generate_skills(t)
        assert len(s) >= 1
        for sk in s: assert sk.name and sk.confidence > 0


class TestTemplate:
    def test_markdown(self):
        s = SkillTemplate(name="Test", description="Desc", triggers=["T"], steps=["S1"], confidence=0.8)
        assert "# Skill: Test" in s.to_markdown() and "80%" in s.to_markdown()


class TestCLI:
    def _r(self, *a):
        from agent_skill_gen.cli import main
        import io; b = io.StringIO(); o = sys.stdout; sys.stdout = b
        try: main(list(a))
        except SystemExit: pass
        finally: sys.stdout = o
        return b.getvalue()
    def test_analyze(self):
        p = _jl(_sample()); o = self._r("analyze",p); os.unlink(p)
        assert "Tool sequences:" in o
    def test_generate_json(self):
        p = _jl(_sample()+_err()); o = self._r("generate",p,"--json"); os.unlink(p)
        d = json.loads(o); assert d["total"] >= 1
    def test_generate_output(self):
        p = _jl(_sample()); d = tempfile.mkdtemp()
        self._r("generate",p,"--output",d); os.unlink(p)
        fs = os.listdir(d); assert len(fs) >= 1
        for f in fs: os.unlink(os.path.join(d,f))
        os.rmdir(d)
