"""每月整理腳本:產生檔案索引、檢查命名規則與失效連結,輸出整理報告。

    python3 scripts/tidy_repo.py > report.md

做三件事:
1. 重新產生 INDEX.md(全倉庫檔案目錄,含超連結與最後更新日期)
2. 檢查檔名規則(空格、過長路徑)與 Markdown 相對連結是否失效
3. 檢查帳號層級:列出缺少描述或主題標籤的公開倉庫

由 .github/workflows/monthly-tidy.yml 每月自動執行,也可手動執行。
只用 Python 標準函式庫。
"""

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "__pycache__"}
INDEX_FILE = ROOT / "INDEX.md"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)[^)]*\)")


def list_files() -> list[Path]:
    return sorted(
        p.relative_to(ROOT)
        for p in ROOT.rglob("*")
        if p.is_file() and not SKIP_PARTS.intersection(p.parts)
    )


def last_commit_date(rel: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%as", "--", str(rel)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return out or "(尚未提交)"
    except Exception:
        return "—"


def build_index(files: list[Path]) -> None:
    lines = [
        "# 檔案索引",
        "",
        "> 由 `scripts/tidy_repo.py` 自動產生(每月一次),請勿手動編輯。",
        "",
    ]
    groups: dict[str, list[Path]] = {}
    for f in files:
        folder = f.parent.as_posix() if f.parent != Path(".") else "(根目錄)"
        groups.setdefault(folder, []).append(f)
    for folder in sorted(groups):
        lines += [f"## {folder}", "", "| 檔案 | 最後更新 |", "| --- | --- |"]
        lines += [
            f"| [{f.name}]({f.as_posix()}) | {last_commit_date(f)} |"
            for f in groups[folder]
        ]
        lines.append("")
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")


def check_naming(files: list[Path]) -> list[str]:
    problems = []
    for f in files:
        path = f.as_posix()
        if " " in path:
            problems.append(f"- `{path}`:檔名含空格(連結會斷,建議改用 `-`)")
        if len(path) > 120:
            problems.append(f"- `{path}`:路徑過長({len(path)} 字元)")
    return problems


def check_links(files: list[Path]) -> list[str]:
    broken = []
    for f in files:
        if f.suffix.lower() != ".md":
            continue
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"```.*?```", "", text, flags=re.S)  # 忽略程式碼區塊
        text = re.sub(r"`[^`\n]*`", "", text)              # 忽略行內程式碼
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (ROOT / f.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"- `{f.as_posix()}` → `{target}`(目標不存在)")
    return broken


def audit_account(owner: str) -> list[str]:
    url = f"https://api.github.com/users/{owner}/repos?per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            repos = json.load(resp)
    except Exception as exc:
        return [f"- (略過:無法存取 GitHub API:{exc})"]
    findings = []
    for repo in repos:
        missing = []
        if not repo.get("description"):
            missing.append("缺少描述")
        if not repo.get("topics"):
            missing.append("缺少主題標籤(topics)")
        if missing:
            findings.append(f"- [{repo['name']}]({repo['html_url']}):{'、'.join(missing)}")
    return findings


def section(title: str, items: list[str], ok_text: str) -> list[str]:
    return [f"## {title}", ""] + (items if items else [f"✅ {ok_text}"]) + [""]


def main() -> None:
    files = list_files()
    build_index(files)
    files = list_files()  # 重新列一次,讓剛產生的 INDEX.md 也被納入檢查

    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "paulchang3")
    report = ["# 每月整理報告", ""]
    report += section(
        "檔案索引", [f"已重新產生 [INDEX.md](INDEX.md),共 {len(files)} 個檔案。"], ""
    )
    report += section("檔名檢查", check_naming(files), "全部符合命名規則")
    report += section("Markdown 連結檢查", check_links(files), "所有相對連結皆有效")
    report += section(f"帳號層級({owner} 的公開倉庫)", audit_account(owner),
                      "所有公開倉庫都有描述與主題標籤")
    report += [
        "## 建議的下一步",
        "",
        "- 有需要深度整理(改名、補連結、重新分類)時,",
        "  在 Claude Code 開啟本倉庫並執行 `/tidy-github`。",
    ]
    print("\n".join(report))


if __name__ == "__main__":
    main()
