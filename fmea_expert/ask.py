"""步驟三:向 FMEA 專家提問(自動附上 Word 知識庫中最相關的段落)。

指令列用法:
    python ask.py "充電過熱失效,S=8 O=4 D=3,請計算 RPN 並判讀"
    python ask.py            # 不帶參數 → 進入互動問答模式

在其他 .py 程式中呼叫:
    from ask import ask
    print(ask("你的問題"))
"""

import json
import math
import os
import sys
from pathlib import Path

try:
    from . import ollama_api
except ImportError:
    import ollama_api

HERE = Path(__file__).resolve().parent
KNOWLEDGE_FILE = HERE / "knowledge.json"
CHAT_MODEL = os.environ.get("FMEA_CHAT_MODEL", "fmea-expert")
EMBED_MODEL = os.environ.get("FMEA_EMBED_MODEL", "bge-m3")


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        raise SystemExit("找不到 knowledge.json,請先執行:python build_knowledge.py")
    return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))


def retrieve(question: str, top_k: int = 4) -> list[dict]:
    """回傳與問題最相關的 top_k 個文件段落(含相似度分數)。"""
    knowledge = _load_knowledge()
    query_vec = ollama_api.embed([question], knowledge["embed_model"])[0]
    scored = [
        {**chunk, "score": _cosine(query_vec, chunk["embedding"])}
        for chunk in knowledge["chunks"]
    ]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:top_k]


def ask(question: str, top_k: int = 4, model: str = CHAT_MODEL) -> str:
    """問一個問題,回傳專家模型的回答(最常用的入口)。"""
    answer, _ = ask_with_sources(question, top_k=top_k, model=model)
    return answer


def ask_with_sources(
    question: str, top_k: int = 4, model: str = CHAT_MODEL
) -> tuple[str, list[dict]]:
    """同 ask(),但連同引用的文件段落一起回傳,方便查核。"""
    sources = retrieve(question, top_k)
    context = "\n\n".join(
        f"【資料 {i}|來源:{c['source']}】\n{c['text']}"
        for i, c in enumerate(sources, 1)
    )
    user_message = (
        "以下是來自使用者 Word 文件的參考資料(可能不完整):\n\n"
        f"{context}\n\n"
        "請根據上述參考資料與你的專業知識回答問題;"
        "計算 RPN 時請逐步列出 S、O、D 與乘積。\n\n"
        f"問題:{question}"
    )
    answer = ollama_api.chat([{"role": "user", "content": user_message}], model)
    return answer, sources


def _interactive() -> None:
    print(f"FMEA 風險管理專家(模型:{CHAT_MODEL},輸入 exit 離開)")
    while True:
        try:
            question = input("\n你:").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question or question.lower() in ("exit", "quit"):
            break
        answer, sources = ask_with_sources(question)
        print("\n專家:", answer)
        cited = ", ".join(sorted({s["source"] for s in sources}))
        print(f"\n(參考文件:{cited})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))
    else:
        _interactive()
