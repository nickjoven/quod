"""prover_backends.py — the model call behind the batch-round protocol (attempt_b.py).

Two backends, one shape. A backend takes a list of requests
  {"custom_id": str, "params": {"model", "max_tokens", "system": [...], "messages": [...], ...}}
and returns, per request, a normalized result
  {"custom_id", "ok": bool, "error": str|None, "text": str, "stop_reason": str,
   "usage": {"input", "output", "cache_write", "cache_read"}, "raw": <verbatim provider result>}
`submit` returns a batch id (the provider's, or a synthetic one), `wait` blocks until it is done,
`results` yields the normalized rows. Spend is the driver's business: it prices `usage` at the
recorded rates, and a local backend reports its wall clock instead of tokens it did not buy.

  anthropic      Message Batches (asynchronous, 50% off); ANTHROPIC_API_KEY (+ ANTHROPIC_WORKSPACE_ID)
  openai-compat  any /v1/chat/completions server (llama.cpp, vLLM, …) — requests run now, in a small
                 thread pool; the "batch" is a local JSON file so re-processing by id works the same way
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import time
import urllib.request


class AnthropicBackend:
    name = "anthropic"

    def __init__(self, model: str):
        import anthropic
        ws = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        self.client = anthropic.Anthropic(default_headers={"anthropic-workspace-id": ws} if ws else None)
        self.model = model

    def model_info(self) -> dict:
        mi = self.client.models.retrieve(self.model)
        return {"created_at": str(getattr(mi, "created_at", None))}

    def submit(self, reqs: list[dict]) -> str:
        return self.client.messages.batches.create(requests=reqs).id

    def wait(self, batch_id: str, poll: int = 30) -> None:
        while self.client.messages.batches.retrieve(batch_id).processing_status != "ended":
            time.sleep(poll)

    def results(self, batch_id: str):
        for res in self.client.messages.batches.results(batch_id):
            raw = res.model_dump() if hasattr(res, "model_dump") else str(res)
            if res.result.type != "succeeded":
                yield {"custom_id": res.custom_id, "ok": False, "error": str(getattr(res.result, "error", ""))[:300],
                       "text": "", "stop_reason": None, "usage": {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}, "raw": raw}
                continue
            m = res.result.message; u = m.usage
            yield {"custom_id": res.custom_id, "ok": True, "error": None,
                   "text": "".join(getattr(c, "text", "") for c in m.content), "stop_reason": m.stop_reason,
                   "usage": {"input": u.input_tokens, "output": u.output_tokens,
                             "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
                             "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0}, "raw": raw}


class OpenAICompatBackend:
    """A local /v1/chat/completions server. Requests run immediately; the batch is a file under
    `store` named by a synthetic id, so `results(batch_id)` re-reads it exactly like a paid batch."""
    name = "openai-compat"

    def __init__(self, model: str, base_url: str, store: str, workers: int = 2, temperature: float = 0.6,
                 timeout_s: int = 900, api_key: str | None = None):
        self.model, self.base_url, self.store = model, base_url.rstrip("/"), store
        self.workers, self.temperature, self.timeout_s = workers, temperature, timeout_s
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "none")
        os.makedirs(store, exist_ok=True)

    def _post(self, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(self.base_url + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                                     method="POST" if body is not None else "GET")
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            return json.loads(r.read())

    def model_info(self) -> dict:
        try:
            ms = self._post("/models")
            ids = [m.get("id") for m in ms.get("data", [])]
            return {"server_models": ids[:8], "created_at": next((str(m.get("created")) for m in ms.get("data", []) if m.get("id") == self.model), None)}
        except Exception as e:  # noqa: BLE001
            return {"created_at": None, "error": type(e).__name__}

    def _one(self, req: dict) -> dict:
        p = req["params"]
        system = "".join(b.get("text", "") for b in p.get("system", []) if isinstance(b, dict))
        body = {"model": self.model, "max_tokens": p.get("max_tokens", 4000), "temperature": self.temperature,
                "messages": ([{"role": "system", "content": system}] if system else []) + p["messages"]}
        t0 = time.monotonic()
        try:
            out = self._post("/chat/completions", body)
            ch = out["choices"][0]; u = out.get("usage", {})
            return {"custom_id": req["custom_id"], "ok": True, "error": None,
                    "text": (ch.get("message") or {}).get("content") or "", "stop_reason": ch.get("finish_reason"),
                    "usage": {"input": u.get("prompt_tokens", 0), "output": u.get("completion_tokens", 0), "cache_write": 0, "cache_read": 0},
                    "wall_s": round(time.monotonic() - t0, 2), "raw": out}
        except Exception as e:  # noqa: BLE001
            return {"custom_id": req["custom_id"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "text": "", "stop_reason": None,
                    "usage": {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}, "wall_s": round(time.monotonic() - t0, 2), "raw": None}

    def submit(self, reqs: list[dict]) -> str:
        bid = f"local_{time.strftime('%Y%m%d-%H%M%S')}_{len(reqs)}_{os.getpid()}_{int(time.monotonic() * 1000) % 100000}"
        with cf.ThreadPoolExecutor(max_workers=self.workers) as ex:
            rows = list(ex.map(self._one, reqs))
        with open(os.path.join(self.store, f"{bid}.json"), "w") as f:
            json.dump(rows, f)
        return bid

    def wait(self, batch_id: str, poll: int = 0) -> None:
        return None

    def results(self, batch_id: str):
        for row in json.load(open(os.path.join(self.store, f"{batch_id}.json"))):
            yield row


def make_backend(kind: str, model: str, **kw):
    if kind == "anthropic":
        return AnthropicBackend(model)
    if kind == "openai-compat":
        return OpenAICompatBackend(model, **kw)
    raise ValueError(kind)
