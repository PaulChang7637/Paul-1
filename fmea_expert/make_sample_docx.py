"""產生一份 FMEA 知識範例 Word 文件(my_docs/FMEA知識範例.docx)。

讓你不必先準備自己的文件,就能把整條流程跑通;
之後把自己的 .docx 放進 my_docs/ 取代它即可。
只用標準函式庫(.docx 本質上是 zip + XML)。
"""

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent / "my_docs" / "FMEA知識範例.docx"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

PARAGRAPHS = [
    "公司風險管理程序書(範例)— ISO 14971 與 FMEA",
    "1. 評分量表:嚴重度 S(1=幾乎無影響,5=需要醫療介入,8=造成永久性傷害,10=可能導致死亡)。",
    "2. 發生度 O(1=極少發生,機率低於十萬分之一;5=偶爾發生,約千分之一;10=幾乎必然發生,高於十分之一)。",
    "3. 可偵測度 D(1=現有管制幾乎一定能偵測;5=有機會偵測;10=現有管制無法偵測)。",
    "4. 本公司風險接受準則:RPN = S × O × D。RPN ≥ 120 為不可接受,必須立即採取風險控制措施;"
    "60 ≤ RPN < 120 為 ALARP 區,需評估進一步降低風險的可行性並由風險管理委員會核決;"
    "RPN < 60 為可接受,納入例行監控。",
    "5. 任何 S ≥ 9 的失效模式,無論 RPN 多少,一律視為不可接受,需執行風險控制。",
    "6. 風險控制措施的優先順序:(a) 本質安全設計;(b) 製造程序或產品本身的防護措施;(c) 安全資訊(標示、說明書、訓練)。",
    "7. 控制措施實施後必須重新評分(殘餘風險評估),並確認未引入新的風險。",
    "附表:失效模式範例(節錄)",
]

TABLE_ROWS = [
    ["失效模式", "S", "O", "D", "RPN", "處置"],
    ["電池充電過熱", "8", "4", "3", "96", "ALARP:評估增加溫度保險絲"],
    ["感測器讀值漂移", "6", "5", "4", "120", "不可接受:增加開機自我校正"],
    ["外殼標籤脫落", "3", "4", "2", "24", "可接受:例行監控"],
]


def _p(text: str) -> str:
    return f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"


def _table(rows: list[list[str]]) -> str:
    xml = ["<w:tbl>"]
    for row in rows:
        xml.append("<w:tr>")
        for cell in row:
            xml.append(f"<w:tc>{_p(cell)}</w:tc>")
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def main() -> None:
    body = "".join(_p(t) for t in PARAGRAPHS) + _table(TABLE_ROWS)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document)
    print(f"已產生範例文件:{OUT}")


if __name__ == "__main__":
    main()
