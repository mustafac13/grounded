"""Local demo page: ask a question, get cited claims or a refusal, click a
citation to read the provision it rests on. One POST endpoint plus one page.

Run:  python app.py                 then open http://127.0.0.1:8000
      python app.py --self-check    offline, fake model, real retrieval

Guards (design note): 20 s model timeout, question length cap, daily request
cap. Passage text is shown with its provision reference and no deep links
(Handbook terms cl. 48/49 not yet re-read). The model sees only collections
marked remote_ok, enforced in answer.py, not here.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer

import answer as ans

TIMEOUT_S = 20
MAX_QUESTION = 400
DAILY_CAP = 200

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grounded</title>
<style>
:root { --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a65; --line:#dedbd2; --accent:#1f5f8b; --warn:#8b4a1f; }
@media (prefers-color-scheme: dark) { :root { --bg:#161615; --fg:#ecebe6; --muted:#9d9b94; --line:#33322e; --accent:#7fb3d9; --warn:#e0a070; } }
body { background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; margin:0; }
main { max-width:720px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.4rem; margin:0 0 4px; } .sub { color:var(--muted); margin:0 0 20px; }
textarea { width:100%; box-sizing:border-box; font:inherit; padding:10px; border:1px solid var(--line);
  border-radius:6px; background:transparent; color:inherit; min-height:72px; }
button { font:inherit; cursor:pointer; }
#ask { margin-top:8px; padding:8px 18px; border:0; border-radius:6px; background:var(--accent); color:var(--bg); }
#ask:disabled { opacity:.6; cursor:wait; }
#status { color:var(--muted); margin:12px 0; min-height:1.5em; }
.claim { margin:0 0 12px; } .cite { margin-left:6px; padding:1px 8px; border:1px solid var(--accent);
  border-radius:10px; background:transparent; color:var(--accent); font-size:.85rem; }
.refusal { border-left:3px solid var(--warn); padding:8px 12px; }
.passage { border:1px solid var(--line); border-radius:6px; padding:10px 12px; margin:8px 0;
  white-space:pre-wrap; font-size:.92rem; }
.passage b { display:block; margin-bottom:4px; } .shown { color:var(--muted); font-size:.85rem; margin-top:20px; }
footer { color:var(--muted); font-size:.8rem; margin-top:32px; }
</style></head><body><main>
<h1>Grounded</h1>
<p class="sub">Questions about FCA PRIN and DISP 1. Every claim cites the provision it rests on; if the provisions do not answer it, it refuses.</p>
<textarea id="q" maxlength="MAXQ" placeholder="How long does a firm have to resolve a complaint?"></textarea>
<button id="ask">Ask</button>
<div id="status" role="status" aria-live="polite"></div>
<div id="out"></div>
<footer>Contains FCA Handbook material, &copy; FCA, reused under the Open Government Licence v3. Not advice.</footer>
</main><script>
const $ = id => document.getElementById(id);
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
async function ask() {
  const q = $("q").value.trim(); if (!q) return;
  $("ask").disabled = true; $("status").textContent = "Working..."; $("out").replaceChildren();
  const t0 = performance.now();
  try {
    const r = await fetch("/ask", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question:q})});
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
    render(d); $("status").textContent = "Done in " + ((performance.now() - t0) / 1000).toFixed(1) + " s.";
  } catch (e) { $("status").textContent = "Error: " + e.message; }
  finally { $("ask").disabled = false; }
}
function render(d) {
  const out = $("out"), byId = Object.fromEntries(d.passages.map(p => [p.id, p]));
  if (d.refusal) { out.append(el("p", "refusal", "Refused: " + d.refusal)); }
  for (const c of d.claims) {
    const p = el("p", "claim", c.text), box = el("div");
    for (const id of c.cites) {
      const b = el("button", "cite", id);
      b.onclick = () => { if (box.firstChild) { box.replaceChildren(); return; }
        const s = byId[id], div = el("div", "passage"); div.append(el("b", null, s.id + (s.status ? " " + s.status : "")), s.text); box.append(div); };
      p.append(b);
    }
    out.append(p, box);
  }
  if (d.invalid) out.append(el("p", "refusal", "The model's output did not pass validation, so nothing is shown."));
  out.append(el("p", "shown", "Provisions shown to the model: " + d.passages.map(p => p.id).join(", ")));
}
$("ask").onclick = ask;
$("q").addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) ask(); });
</script></body></html>""".replace("MAXQ", str(MAX_QUESTION))


def make_handler(conn, emb, call):
    used = {"day": date.today(), "n": 0}

    class H(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, d: dict) -> None:
            self._send(code, json.dumps(d).encode(), "application/json")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/ask":
                return self._json(404, {"error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", 0))
                q = json.loads(self.rfile.read(min(n, 4096)) or b"{}").get("question", "")
            except (ValueError, AttributeError):
                return self._json(400, {"error": "send JSON with a question"})
            q = q.strip() if isinstance(q, str) else ""
            if not q or len(q) > MAX_QUESTION:
                return self._json(400, {"error": f"question must be 1 to {MAX_QUESTION} characters"})
            if used["day"] != date.today():
                used.update(day=date.today(), n=0)
            if used["n"] >= DAILY_CAP:
                return self._json(429, {"error": "daily request cap reached"})
            used["n"] += 1
            passages = ans.context(conn, q, emb)
            try:
                rec = ans.answer(q, passages, call=call)
            except subprocess.TimeoutExpired:
                return self._json(504, {"error": f"the model did not answer within {TIMEOUT_S} s"})
            except (RuntimeError, PermissionError) as e:
                return self._json(502, {"error": str(e)[:200]})
            p = rec["parsed"]
            self._json(200, {"refusal": p["refusal"] if p else None, "claims": p["claims"] if p else [],
                             "invalid": p is None,
                             "passages": [{k: x[k] for k in ("id", "status", "text")} for x in passages]})

        def log_message(self, fmt, *args):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    return H


def live_call(system, user, model):
    return ans.call_claude(system, user, model, timeout=TIMEOUT_S)


def serve(port: int, call=live_call, ready: threading.Event | None = None, box: dict | None = None) -> None:
    """Connection and server are built in the thread that serves them (SQLite
    connections are thread-bound). One request at a time."""
    # ponytail: single-threaded server, fine for a one-person demo; ThreadingHTTPServer + per-thread conn if shared.
    import retrieve as rt
    httpd = HTTPServer(("127.0.0.1", port), make_handler(rt.connect(), rt.Embedder(), call))
    if box is not None:
        box["httpd"] = httpd
    if ready:
        ready.set()
    httpd.serve_forever()


def _self_check() -> None:
    import urllib.error
    import urllib.request

    good = {"refusal": None, "claims": [{"text": "Eight weeks.", "cites": []}]}

    def fake(system, user, model):
        if "<question>complaint hang</question>" in user:
            raise subprocess.TimeoutExpired("claude", TIMEOUT_S)
        first = user.split('<passage id="')[1].split('"')[0]   # cite the top passage actually shown
        good["claims"][0]["cites"] = [first]
        return {"text": json.dumps(good)}

    ready, box = threading.Event(), {}
    threading.Thread(target=serve, args=(0, fake, ready, box), daemon=True).start()
    ready.wait(120)
    base = f"http://127.0.0.1:{box['httpd'].server_address[1]}"

    def post(body):
        req = urllib.request.Request(base + "/ask", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    with urllib.request.urlopen(base + "/", timeout=10) as r:
        page = r.read().decode()
    assert "Grounded" in page and "&copy; FCA" in page and "textContent" in page and "innerHTML" not in page

    code, d = post({"question": "how long does a firm have to send a final response to a complaint"})
    assert code == 200 and not d["invalid"] and d["refusal"] is None, (code, d)
    assert len(d["passages"]) == ans.K and d["claims"][0]["cites"][0] == d["passages"][0]["id"], d
    assert all(p["text"] for p in d["passages"])
    # Every cited id has its passage in the response, so the page can always open it.
    assert {c for cl in d["claims"] for c in cl["cites"]} <= {p["id"] for p in d["passages"]}

    assert post({"question": ""})[0] == 400
    assert post({"question": "x" * (MAX_QUESTION + 1)})[0] == 400
    assert post({"nope": 1})[0] == 400
    code, d = post({"question": "complaint hang"})
    assert code == 504 and "20 s" in d["error"], (code, d)
    global DAILY_CAP
    # Two requests reached the counter so far (the answer and the hang). A cap of 3
    # admits exactly one more, then refuses: the boundary, not just "cap 0 refuses".
    saved, DAILY_CAP = DAILY_CAP, 3
    try:
        assert post({"question": "complaint"})[0] == 200
        assert post({"question": "complaint"})[0] == 429
    finally:
        DAILY_CAP = saved
    assert post({"question": "complaint"})[0] == 200
    box["httpd"].shutdown()
    print("self-check passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    print(f"Grounded on http://127.0.0.1:{a.port}  (Ctrl+C to stop)")
    serve(a.port)


if __name__ == "__main__":
    sys.exit(main())
