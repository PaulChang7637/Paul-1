"""與本機 Ollama 伺服器溝通的最小 API 層(只用 Python 標準函式庫)。

預設連到 http://127.0.0.1:11434,可用環境變數 OLLAMA_HOST 覆寫
(與 ollama CLI 使用同一個變數)。
"""

import json
import os
import urllib.request


def base_url() -> str:
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    if "://" not in host:
        host = "http://" + host
    return host.rstrip("/")


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        base_url() + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.load(resp)


def embed(texts: list[str], model: str) -> list[list[float]]:
    """把一批文字轉成向量(語意指紋)。"""
    return _post("/api/embed", {"model": model, "input": texts})["embeddings"]


def chat(messages: list[dict], model: str) -> str:
    """送出對話訊息,回傳模型的回答文字。"""
    resp = _post("/api/chat", {"model": model, "messages": messages, "stream": False})
    return resp["message"]["content"]
