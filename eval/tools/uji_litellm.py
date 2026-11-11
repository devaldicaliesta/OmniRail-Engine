#!/usr/bin/env python3
"""Uji LiteLLM dengan guardrail Presidio terhadap server tiruan.

    python eval/tools/uji_litellm.py
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

AKAR = Path(__file__).resolve().parents[2]
PORT_MOCK, PORT_PRESIDIO, PORT_LITELLM = 9100, 9200, 4000
KUNCI = "sk-uji-omnirail"
JEDA_MOCK = 0.05
diterima: list[dict] = []


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        diterima.append({"path": self.path, "body": body})
        time.sleep(JEDA_MOCK)
        teks = "Diterima: " + _teks_terakhir(body["messages"])
        if body.get("stream") and not self.path.endswith("/messages"):
            return self._stream(body["model"], teks)
        if self.path.endswith("/messages"):
            jawab = {"id": "msg_1", "type": "message", "role": "assistant", "model": body["model"],
                     "content": [{"type": "text", "text": teks}], "stop_reason": "end_turn",
                     "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}
        else:
            jawab = {"id": "c1", "object": "chat.completion", "created": 0, "model": body["model"],
                     "choices": [{"index": 0, "finish_reason": "stop",
                                  "message": {"role": "assistant", "content": teks}}],
                     "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
        data = json.dumps(jawab).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


    def _stream(self, model, teks):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        potongan = [teks[i:i + 7] for i in range(0, len(teks), 7)]
        for i, isi in enumerate(potongan + [None]):
            delta = {"content": isi} if isi is not None else {}
            chunk = {"id": "c1", "object": "chat.completion.chunk", "created": 0, "model": model,
                     "choices": [{"index": 0, "delta": delta, "finish_reason": None if isi is not None else "stop"}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.close_connection = True


def _teks_terakhir(pesan):
    isi = pesan[-1]["content"]
    return isi if isinstance(isi, str) else " ".join(b.get("text", "") for b in isi)


def layanan_presidio():
    from flask import Flask, jsonify, request
    from presidio_analyzer import RecognizerResult
    from presidio_anonymizer import AnonymizerEngine

    import baseline_presidio

    analis = baseline_presidio._mesin()
    anonim = AnonymizerEngine()
    app = Flask("presidio")

    @app.post("/analyze")
    def analyze():
        q = request.get_json()
        hasil = analis.analyze(text=q["text"], language="id")
        return jsonify([{"entity_type": h.entity_type, "start": h.start, "end": h.end, "score": h.score}
                        for h in hasil if h.score >= baseline_presidio.KONFIGURASI["ambang"]])

    @app.post("/anonymize")
    def anonymize():
        q = request.get_json()
        hasil = [RecognizerResult(r["entity_type"], r["start"], r["end"], r["score"]) for r in q["analyzer_results"]]
        out = anonim.anonymize(text=q["text"], analyzer_results=hasil)
        return jsonify({"text": out.text, "items": [
            {"start": i.start, "end": i.end, "entity_type": i.entity_type, "text": i.text, "operator": i.operator}
            for i in out.items]})

    return app


def mulai_layanan():
    mock = ThreadingHTTPServer(("127.0.0.1", PORT_MOCK), Mock)
    threading.Thread(target=mock.serve_forever, daemon=True).start()
    from werkzeug.serving import make_server

    presidio = make_server("127.0.0.1", PORT_PRESIDIO, layanan_presidio(), threaded=True)
    threading.Thread(target=presidio.serve_forever, daemon=True).start()


def mulai_litellm(folder: Path, scope: str | None, guardrail: bool = True) -> subprocess.Popen:
    konfig = folder / "litellm.yaml"
    baris_scope = f"\n      presidio_filter_scope: {scope}" if scope else ""
    blok_guardrail = f"""guardrails:
  - guardrail_name: presidio-id
    litellm_params:
      guardrail: presidio
      mode: pre_call
      output_parse_pii: true
      presidio_language: id
      default_on: true{baris_scope}
""" if guardrail else ""
    konfig.write_text(f"""
model_list:
  - model_name: mock-openai
    litellm_params: {{model: openai/mock, api_base: "http://127.0.0.1:{PORT_MOCK}/v1", api_key: dummy}}
  - model_name: mock-claude
    litellm_params: {{model: anthropic/claude-mock, api_base: "http://127.0.0.1:{PORT_MOCK}", api_key: dummy}}
{blok_guardrail}general_settings:
  master_key: {KUNCI}
""")
    env = dict(os.environ, LITELLM_LOCAL_MODEL_COST_MAP="True",
               PRESIDIO_ANALYZER_API_BASE=f"http://127.0.0.1:{PORT_PRESIDIO}",
               PRESIDIO_ANONYMIZER_API_BASE=f"http://127.0.0.1:{PORT_PRESIDIO}",
               NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    log = open(folder / "litellm.log", "w")
    perintah = Path(sys.executable).parent / "litellm"
    perintah = str(perintah) if perintah.exists() else shutil.which("litellm")
    proses = subprocess.Popen([perintah, "--config", str(konfig),
                               "--port", str(PORT_LITELLM), "--num_workers", "1"],
                              env=env, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            if httpx.get(f"http://127.0.0.1:{PORT_LITELLM}/health/liveliness", timeout=1).status_code == 200:
                return proses
        except httpx.HTTPError:
            pass
        time.sleep(1)
    proses.kill()
    raise SystemExit(f"LiteLLM tidak menyala, lihat {folder / 'litellm.log'}")


KLIEN = httpx.Client(base_url=f"http://127.0.0.1:{PORT_LITELLM}", timeout=30,
                     headers={"Authorization": f"Bearer {KUNCI}", "x-api-key": KUNCI})


def chat(model, teks, **extra):
    diterima.clear()
    r = KLIEN.post("/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": teks}], **extra})
    if extra.get("stream"):
        bagian = []
        for baris in r.text.splitlines():
            if baris.startswith("data: ") and baris != "data: [DONE]":
                delta = json.loads(baris[6:])["choices"][0]["delta"].get("content")
                bagian.append(delta or "")
        return r.status_code, "".join(bagian), _ke_upstream()
    jawab = r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else r.text[:200]
    return r.status_code, jawab, _ke_upstream()


def messages_native(teks):
    diterima.clear()
    r = KLIEN.post("/v1/messages", headers={"anthropic-version": "2023-06-01"},
                   json={"model": "mock-claude", "max_tokens": 100, "messages": [{"role": "user", "content": teks}]})
    jawab = r.json()["content"][0]["text"] if r.status_code == 200 else r.text[:200]
    return r.status_code, jawab, _ke_upstream()


def _ke_upstream():
    return _teks_terakhir(diterima[-1]["body"]["messages"]) if diterima else None


def skenario():
    hasil = []

    def catat(nama, status, jawab, upstream, bocor, pulih):
        hasil.append({"skenario": nama, "status": status, "ke_provider": upstream, "jawaban": jawab,
                      "nilai_asli_sampai_provider": bocor, "nilai_dipulihkan": pulih})

    email, nik = "budi@example.com", "3273011503900001"
    teks = f"Email saya {email} dan {email}, NIK {nik}"
    for nama, fungsi in [("openai, non-streaming", lambda: chat("mock-openai", teks)),
                         ("anthropic lewat /v1/chat/completions", lambda: chat("mock-claude", teks)),
                         ("anthropic native /v1/messages", lambda: messages_native(teks)),
                         ("openai, stream=true", lambda: chat("mock-openai", teks, stream=True))]:
        s, j, u = fungsi()
        catat(nama, s, j, u, bool(u) and (email in u or nik in u), email in j and nik in j)

    s, j, u = chat("mock-openai", f"Balas ke <EMAIL_ADDRESS_1> saja, jangan ke {email}")
    catat("token buatan pengguna di input", s, j, u, bool(u) and email in u,
          j.count(email) == 1 and "<EMAIL_ADDRESS_1>" in j)

    kredensial = {
        "midtrans": "Mid-server-AbCdEf1234567890xYz",
        "xendit": "xnd_production_P8aZ3kL0qWe9RtYu2IoPaSdFgHjKl1Zx",
        "telegram": "1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsawE",
        "postgres": "postgres://app:s3cret@db:5432/x",
        "aws": "AKIAIOSFODNN7EXAMPLE",
    }
    for jenis, nilai in kredensial.items():
        s, j, u = chat("mock-openai", f"Kenapa error ini muncul? key={nilai}")
        hasil.append({"skenario": f"credentials {jenis}", "status": s, "ke_provider": u,
                      "diblokir": s >= 400, "nilai_asli_sampai_provider": bool(u) and nilai in u})
    return hasil


async def _beban(url, headers, body, laju, durasi):
    async with httpx.AsyncClient(timeout=30, headers=headers) as c:
        jadwal0 = time.perf_counter()
        latensi = []

        async def satu(t_jadwal):
            await asyncio.sleep(max(0, t_jadwal - time.perf_counter()))
            r = await c.post(url, json=body)
            r.raise_for_status()
            latensi.append(time.perf_counter() - t_jadwal)

        await asyncio.gather(*(satu(jadwal0 + i / laju) for i in range(int(laju * durasi))))
    latensi.sort()
    return {"n": len(latensi), "p50_ms": round(statistics.median(latensi) * 1000, 1),
            "p99_ms": round(latensi[int(0.99 * (len(latensi) - 1))] * 1000, 1)}


def latensi(laju=10, durasi=20):
    isi = ("Ringkas percakapan CS berikut. " * 30)[:900] + " Email budi@example.com, NIK 3273011503900001."
    body = {"model": "mock", "messages": [{"role": "user", "content": isi}]}
    langsung = asyncio.run(_beban(f"http://127.0.0.1:{PORT_MOCK}/v1/chat/completions", {}, body, laju, durasi))
    body = dict(body, model="mock-openai")
    lewat = asyncio.run(_beban(f"http://127.0.0.1:{PORT_LITELLM}/v1/chat/completions",
                               {"Authorization": f"Bearer {KUNCI}"}, body, laju, durasi))
    return {"input_karakter": len(isi), "laju_rps": laju, "durasi_detik": durasi, "jeda_mock_ms": JEDA_MOCK * 1000,
            "langsung_ke_mock": langsung, "lewat_proxy": lewat,
            "overhead_p50_ms": round(lewat["p50_ms"] - langsung["p50_ms"], 1),
            "overhead_p99_ms": round(lewat["p99_ms"] - langsung["p99_ms"], 1)}


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ.pop(k, None)
    mulai_layanan()
    import importlib.metadata as md

    laporan = {
        "versi": {p: md.version(p) for p in ("litellm", "presidio-analyzer", "presidio-anonymizer")},
        "waktu": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    for nama, scope, guardrail in [("default", None, True), ("presidio_filter_scope_input", "input", True),
                                   ("tanpa_guardrail", None, False)]:
        folder = Path(tempfile.mkdtemp(prefix="uji-litellm-"))
        proses = mulai_litellm(folder, scope, guardrail)
        try:
            laporan[nama] = {} if not guardrail else {"skenario": skenario()}
            if scope or not guardrail:
                laporan[nama]["latensi"] = latensi()
        finally:
            proses.terminate()
            proses.wait()
    keluar = AKAR / "eval" / "results" / "t005-litellm.json"
    keluar.write_text(json.dumps(laporan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(laporan, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
