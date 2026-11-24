"""Judge vs human agreement on claim support. Matches each '## qid run R claim N'
heading in a run's human_sample.md to the judge's 'supported' label for that
claim in judgements.jsonl, and lists every disagreement.

Run:  python judge_agreement.py eval/runs/dev-v1 eval/runs/heldout-v1
      python judge_agreement.py --self-check
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from evaluate import wilson

HEAD = re.compile(r"^## (\S+) run (\d+) claim (\d+)$.*?^supported: *(\w*)", re.M | re.S)


def compare(run_dir: Path) -> list[dict]:
    judge = {(j["qid"], j["run"]): j["judge"]["claims"]
             for j in map(json.loads, (run_dir / "judgements.jsonl").read_text(encoding="utf-8").splitlines())}
    out = []
    for qid, run, n, human in HEAD.findall((run_dir / "human_sample.md").read_text(encoding="utf-8")):
        if human not in ("yes", "no"):
            raise ValueError(f"unlabelled or bad label: {qid} run {run} claim {n}: {human!r}")
        j = judge[(qid, int(run))][int(n) - 1]["supported"]
        out.append({"id": f"{qid} run {run} claim {n}", "human": human == "yes", "judge": j})
    return out


def report(rows: list[dict]) -> str:
    agree = sum(r["human"] == r["judge"] for r in rows)
    lo, hi = wilson(agree, len(rows))
    L = [f"agreement {agree}/{len(rows)} [{lo:.2f}-{hi:.2f}]",
         f"  both supported {sum(r['human'] and r['judge'] for r in rows)}, "
         f"both unsupported {sum(not r['human'] and not r['judge'] for r in rows)}, "
         f"judge stricter {sum(r['human'] and not r['judge'] for r in rows)}, "
         f"judge more lenient {sum(not r['human'] and r['judge'] for r in rows)}"]
    L += [f"  DISAGREE {r['id']}: human {'yes' if r['human'] else 'no'}, judge {'yes' if r['judge'] else 'no'}"
          for r in rows if r["human"] != r["judge"]]
    return "\n".join(L)


def _self_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "judgements.jsonl").write_text(
            # a1's two judge labels differ, so reading the wrong claim index changes the result.
            json.dumps({"qid": "a1", "run": 1, "judge": {"claims": [{"supported": False}, {"supported": True}]}}) + "\n"
            + json.dumps({"qid": "a2", "run": 3, "judge": {"claims": [{"supported": False}]}}) + "\n", encoding="utf-8")
        sample = ("## a1 run 1 claim 1\n\nClaim: x\n\nsupported: no\n\n"
                  "## a1 run 1 claim 2\n\nClaim: y\n\nsupported: no\n\n"
                  "## a2 run 3 claim 1\n\nClaim: z\n\nsupported: no\n")
        (d / "human_sample.md").write_text(sample, encoding="utf-8")
        rows = compare(d)
        # Claim numbers index the right judge label: a1 claim 2 is the disagreement, not a1 claim 1.
        assert [r["human"] == r["judge"] for r in rows] == [True, False, True], rows
        out = report(rows)
        assert out.startswith("agreement 2/3"), out
        assert "judge more lenient 1" in out and "judge stricter 0" in out, out
        assert "DISAGREE a1 run 1 claim 2: human no, judge yes" in out, out
        assert "both unsupported 2" in out and "both supported 0" in out, out
        # Flip the disagreeing human label: the count must follow it.
        (d / "human_sample.md").write_text(sample.replace("supported: no\n\n## a2", "supported: yes\n\n## a2"),
                                           encoding="utf-8")
        assert report(compare(d)).startswith("agreement 3/3"), report(compare(d))
        # An unlabelled claim stops the count instead of being skipped.
        (d / "human_sample.md").write_text(sample.replace("supported: no\n", "supported:\n", 1), encoding="utf-8")
        try:
            compare(d)
            raise SystemExit("unlabelled claim was counted")
        except ValueError:
            pass
    print("self-check passed")


def main() -> None:
    if "--self-check" in sys.argv:
        return _self_check()
    every = []
    for arg in sys.argv[1:]:
        rows = compare(Path(arg))
        every += rows
        print(f"{Path(arg).name}: {report(rows)}")
    if len(sys.argv) > 2:
        print(f"pooled: {report(every)}")


if __name__ == "__main__":
    sys.exit(main())
