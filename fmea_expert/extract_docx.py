"""從 .docx 檔抽取文字(段落與表格),只用 Python 標準函式庫。

.docx 其實是一個 zip 壓縮檔,主要內容在 word/document.xml。
表格每一列會被轉成「儲存格1 | 儲存格2 | ...」的一行文字,
FMEA 文件常見的表格因此也能被知識庫使用。

也可以直接執行來預覽抽取結果:
    python extract_docx.py my_docs/某文件.docx
"""

import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _paragraph_text(p) -> str:
    return "".join(t.text or "" for t in p.iter(W + "t")).strip()


def extract_lines(docx_path: str) -> list[str]:
    """回傳文件的文字行;表格列轉成「a | b | c」格式。"""
    with zipfile.ZipFile(docx_path) as z:
        root = ET.fromstring(z.read("word/document.xml"))

    lines: list[str] = []
    body = root.find(W + "body")
    for element in body:
        if element.tag == W + "p":
            text = _paragraph_text(element)
            if text:
                lines.append(text)
        elif element.tag == W + "tbl":
            for row in element.iter(W + "tr"):
                cells = []
                for cell in row.iter(W + "tc"):
                    cell_text = " ".join(
                        _paragraph_text(p) for p in cell.iter(W + "p")
                    ).strip()
                    cells.append(cell_text)
                if any(cells):
                    lines.append(" | ".join(cells))
    return lines


def chunk_lines(lines: list[str], max_chars: int = 600) -> list[str]:
    """把文字行合併成適合做向量檢索的小段(每段約 max_chars 字元)。"""
    chunks: list[str] = []
    buffer = ""
    for line in lines:
        if buffer and len(buffer) + len(line) + 1 > max_chars:
            chunks.append(buffer)
            buffer = ""
        while len(line) > max_chars:  # 單行過長時硬切
            chunks.append(line[:max_chars])
            line = line[max_chars:]
        buffer = (buffer + "\n" + line).strip() if buffer else line
    if buffer:
        chunks.append(buffer)
    return chunks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(0)
    for path in sys.argv[1:]:
        print(f"===== {path} =====")
        for line in extract_lines(path):
            print(line)
