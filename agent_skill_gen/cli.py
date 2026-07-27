"""CLI for agent-skill-gen."""

import sys, json, os, argparse
from agent_skill_gen.parser import parse_traces, parse_traces_json
from agent_skill_gen.extractor import generate_skills, extract_all


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="agent-skill-gen", description="Auto-generate skills from agent conversation logs")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("generate", help="Generate skills"); p.add_argument("traces"); p.add_argument("--output"); p.add_argument("--json", action="store_true"); p.add_argument("--min-confidence", type=float, default=0.5)
    p2 = sub.add_parser("analyze", help="Show patterns"); p2.add_argument("traces")
    args = parser.parse_args(argv)
    try:
        entries = parse_traces(args.traces) if args.traces.endswith(".jsonl") else parse_traces_json(args.traces)
        if not entries: print("No trace entries found.", file=sys.stderr); sys.exit(1)
        if args.command == "analyze":
            pat = extract_all(entries)
            print(f"Traces: {len(entries)} entries\nTool sequences: {len(pat['tool_sequences'])}\nError recoveries: {len(pat['error_recoveries'])}\nRepeated tasks: {len(pat['repeated_tasks'])}")
            if pat["tool_sequences"]:
                print("\nTop sequences:")
                from collections import Counter
                for seq, count in Counter(pat["tool_sequences"]).most_common(3): print(f"  [{count}x] {' -> '.join(seq)}")
        elif args.command == "generate":
            skills = [s for s in generate_skills(entries) if s.confidence >= args.min_confidence]
            if args.json:
                print(json.dumps({"total":len(skills),"skills":[{"name":s.name,"description":s.description,"confidence":s.confidence,"pattern":s.source_pattern} for s in skills]}, ensure_ascii=False, indent=2))
            elif args.output:
                os.makedirs(args.output, exist_ok=True)
                for s in skills:
                    with open(os.path.join(args.output, s.name.lower().replace(" ","-")[:50]+".md"), "w", encoding="utf-8") as f: f.write(s.to_markdown())
                print(f"Generated {len(skills)} skills -> {args.output}")
            else:
                print(f"Generated {len(skills)} skills:")
                for s in skills[:10]: print(f"\n  [{s.source_pattern}] {s.name} (confidence={s.confidence:.0%})\n    {s.description[:100]}")
        else: parser.print_help()
    except Exception as e: print(f"Error: {e}", file=sys.stderr); sys.exit(1)


if __name__ == "__main__": main()
