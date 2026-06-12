"""步驟四範例:在「你自己的 .py 程式」中呼叫 FMEA 專家。

本檔可直接執行: python example_usage.py

若你的程式放在其他資料夾,匯入前先把本資料夾加進路徑:
    import sys
    sys.path.append(r"C:\\path\\to\\Paul\\fmea_expert")   # 改成你的實際路徑
    from ask import ask, ask_with_sources
"""

from ask import ask, ask_with_sources

# ── 情境 1:批次計算 —— 把一批失效模式交給專家逐一評估 ──────────────
failure_modes = [
    {"名稱": "電池充電過熱", "S": 8, "O": 4, "D": 3},
    {"名稱": "韌體更新中斷導致無法開機", "S": 7, "O": 3, "D": 5},
]

for fm in failure_modes:
    question = (
        f"失效模式「{fm['名稱']}」,S={fm['S']}、O={fm['O']}、D={fm['D']}。"
        "請計算 RPN,依公司準則判定風險等級,並建議一項控制措施。"
    )
    print("=" * 60)
    print("問題:", question)
    print(ask(question))

# ── 情境 2:知識查詢 —— 答案來自你的 Word 文件,並列出引用來源 ──────
print("=" * 60)
answer, sources = ask_with_sources("依據公司準則,RPN 多少以上是不可接受?需要做什麼?")
print(answer)
print("\n引用段落:")
for s in sources:
    print(f"  [{s['score']:.3f}] {s['source']}:{s['text'][:40]}...")
