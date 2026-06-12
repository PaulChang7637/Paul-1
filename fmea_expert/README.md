# FMEA 風險管理計算專家 — 用你的 Word 文件打造本機 AI 專家

用幾份 Word 文件(.docx)+ 本機 Ollama,做出一個「ISO 14971 FMEA
風險管理計算專家」,可以在終端機問答,也可以在任何 .py 程式中呼叫。
**全程在你的電腦上執行,文件內容不會離開本機。**

## 運作原理(先看懂這 30 秒)

「幾份 Word 文件」不足以真正微調(重新訓練權重)一個模型——那需要
數百筆以上的問答資料與 GPU。這個範例用的是業界標準做法,效果相同:

1. **自訂專家模型**:用 `Modelfile` 把 FMEA 專業規則(RPN 計算、
   風險判讀、ISO 14971 控制措施順序)燒進系統提示詞,
   `ollama create` 之後你的電腦上就有一個叫 `fmea-expert` 的模型。
2. **RAG 知識庫**:把你的 Word 文件抽出文字(含表格)、切成小段、
   轉成向量。提問時自動找出最相關的段落,連同問題一起交給模型,
   所以它能依據**你公司的準則**回答,並標明出處。

```
你的 .docx ──► build_knowledge.py ──► knowledge.json(向量知識庫)
                                            │
你的問題 ────────► ask.py ──(問題+相關段落)──► fmea-expert 模型 ──► 回答
```

所有程式只用 Python 標準函式庫,不需要 `pip install` 任何套件。

## 逐步操作(在你自己的電腦上)

### 步驟 0|前置:安裝 Ollama 並下載兩個模型

到 https://ollama.com 下載安裝(macOS / Windows 安裝後會自動在背景執行),
然後在終端機:

```sh
ollama pull qwen2.5:3b   # 對話模型,約 1.9GB,中文能力佳
ollama pull bge-m3       # 嵌入(向量)模型,約 1.2GB,支援中文檢索
```

> 電腦規格較好(16GB RAM 以上)可改用 `qwen2.5:7b`,
> 並把 `Modelfile` 第一行 `FROM` 改掉。

### 步驟 1|建立你的專家模型

在本資料夾(`fmea_expert/`)執行:

```sh
ollama create fmea-expert -f Modelfile
ollama run fmea-expert "S=8 O=4 D=3,RPN 是多少?"   # 測試一下
```

成功後 `ollama list` 會看到 `fmea-expert` —— 這就是你專屬的小模型。
想改它的個性或準則,編輯 `Modelfile` 的 `SYSTEM` 段落後重新 create 即可。

### 步驟 2|放入 Word 文件,建立知識庫

把你的 FMEA 程序書、風險接受準則、評分量表等 `.docx` 放進 `my_docs/`。
還沒有文件?先產生一份範例:

```sh
python make_sample_docx.py     # 產生 my_docs/FMEA知識範例.docx
python build_knowledge.py      # 抽取文字 → 切塊 → 向量化 → knowledge.json
```

之後文件有新增或修改,重新跑一次 `build_knowledge.py` 就好。

### 步驟 3|開始提問

```sh
# 單次提問
python ask.py "充電過熱失效,S=8 O=4 D=3,請計算 RPN 並依公司準則判讀"

# 互動模式(連續問答)
python ask.py
```

### 步驟 4|在其他 .py 程式中呼叫

```python
import sys
sys.path.append(r"C:\path\to\Paul\fmea_expert")   # 改成你的實際路徑

from ask import ask, ask_with_sources

answer = ask("感測器漂移 S=6 O=5 D=4,請評估")
print(answer)

# 需要查核引用來源時:
answer, sources = ask_with_sources("RPN 多少以上不可接受?")
```

完整範例見 `example_usage.py`(可直接 `python example_usage.py` 執行)。

## 常見問題

- **回答品質不好?** 換大一點的基底模型(`Modelfile` 的 `FROM qwen2.5:7b`
  後重新 `ollama create`),或檢查 `python extract_docx.py my_docs/你的文件.docx`
  的抽取結果是否完整。
- **想換模型名稱?** 環境變數 `FMEA_CHAT_MODEL`、`FMEA_EMBED_MODEL` 可覆寫,
  不用改程式。
- **knowledge.json 是什麼?** 文件段落 + 向量的快取檔。它和 `my_docs/`
  都被 `.gitignore` 排除,**你的公司文件不會被提交進 Git**。
- **之後想「真正微調」?** 等你累積了幾百筆「問題→標準答案」資料,
  可用 Unsloth(Google Colab 免費 GPU 即可)做 LoRA 微調,匯出 GGUF 後
  把 `Modelfile` 的 `FROM` 指向該檔案,其餘流程完全不變。
- **檔案結構**:`ollama_api.py`(API 層)→ `extract_docx.py`(讀 Word)→
  `build_knowledge.py`(建知識庫)→ `ask.py`(檢索+提問)。
  每個檔案都很短,建議照這個順序讀一遍。
