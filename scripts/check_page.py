#!/usr/bin/env python3
"""页面体检脚本：零依赖，只用标准库，输出 Markdown 报告。

用法：
    python check_page.py index.html
    python check_page.py ./pages
    python check_page.py ./pages --md report.md

检查项（硬性）：
    DOCTYPE / html lang / meta viewport / img alt / 重复 id / 标签闭合
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class PageParser(HTMLParser):
    """收集标签闭合情况、img、id、内联样式、标题等。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.unclosed: list[tuple[str, int]] = []
        self.mismatched: list[tuple[str, int, str]] = []
        self.images: list[tuple[int, bool]] = []          # (行号, 是否有 alt)
        self.ids: list[tuple[str, int]] = []
        self.inline_styles: list[int] = []
        self.h1_count = 0
        self.has_lang = False
        self.doctype = False
        self.viewport = ""
        self.title = ""
        self._in_title = False
        self.headings: list[tuple[int, int]] = []        # (级别, 行号)
        self._current_heading: int | None = None

    # -- 标签 --------------------------------------------------------------
    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower().startswith("doctype html"):
            self.doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line = self.getpos()[0]
        attr = {k.lower(): (v or "") for k, v in attrs}

        if tag == "html":
            self.has_lang = bool(attr.get("lang", "").strip())
        elif tag == "meta":
            if attr.get("name", "").lower() == "viewport":
                self.viewport = attr.get("content", "")
        elif tag == "img":
            self.images.append((line, "alt" in attr))
        elif tag == "title":
            self._in_title = True

        if "id" in attr and attr["id"].strip():
            self.ids.append((attr["id"].strip(), line))
        if "style" in attr and attr["style"].strip():
            self.inline_styles.append(line)

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.headings.append((level, line))
            # 校验标题层级是否跳级
            if level == 1:
                self.h1_count += 1

        if tag not in VOID_TAGS:
            self.stack.append((tag, line))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # 自闭合写法 <img />，只处理属性收集，不入栈
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        line = self.getpos()[0]
        if tag == "title":
            self._in_title = False
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.mismatched.append((tag, line, "多余的结束标签"))
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        # 栈中查找同名标签
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for orphan, orphan_line in self.stack[i + 1:]:
                    self.unclosed.append((orphan, orphan_line))
                del self.stack[i:]
                return
        self.mismatched.append((tag, line, "结束标签与开始标签不匹配"))

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data.strip()

    # -- 结果 --------------------------------------------------------------
    def finish(self) -> None:
        for tag, line in self.stack:
            self.unclosed.append((tag, line))


def check_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = PageParser()
    parser.feed(text)
    parser.close()
    parser.finish()

    problems: list[tuple[str, str]] = []   # (级别, 描述)
    passed: list[str] = []

    # 1. DOCTYPE
    if parser.doctype:
        passed.append("文档声明 `<!DOCTYPE html>` 存在")
    else:
        problems.append(("必修", "缺少 `<!DOCTYPE html>`，页面会进入怪异模式"))

    # 2. html lang
    if parser.has_lang:
        passed.append("`<html lang>` 已声明语言")
    else:
        problems.append(("必修", "`<html>` 缺少 `lang` 属性，建议写 `lang=\"zh-CN\"`"))

    # 3. viewport
    if "width=device-width" in parser.viewport.replace(" ", ""):
        passed.append("`meta viewport` 已设置且包含 `width=device-width`")
    elif parser.viewport:
        problems.append(("必修", f"`meta viewport` 内容为 `{parser.viewport}`，建议 "
                                "`width=device-width, initial-scale=1`"))
    else:
        problems.append(("必修", "缺少 `meta viewport`，移动端会按 980px 缩放显示"))

    # 4. img alt
    missing_alt = [line for line, has_alt in parser.images if not has_alt]
    if not parser.images:
        passed.append("页面内没有 `img`，无需检查 alt")
    elif not missing_alt:
        passed.append(f"{len(parser.images)} 个 `img` 都带 `alt`")
    else:
        for line in missing_alt:
            problems.append(("必修", f"第 {line} 行 `img` 缺少 `alt`，装饰图请写 `alt=\"\"`"))

    # 5. 重复 id
    seen: dict[str, int] = {}
    dup = []
    for id_value, line in parser.ids:
        if id_value in seen:
            dup.append((id_value, seen[id_value], line))
        else:
            seen[id_value] = line
    if not parser.ids:
        problems.append(("建议", "页面没有任何 `id`，如果有锚点跳转需求需要补充"))
    elif not dup:
        passed.append(f"{len(parser.ids)} 个 `id` 均唯一")
    else:
        for id_value, first, line in dup:
            problems.append(("必修", f"`id=\"{id_value}\"` 重复：第 {first} 行与第 {line} 行"))

    # 6. 标签闭合
    if parser.unclosed:
        for tag, line in parser.unclosed:
            problems.append(("必修", f"`<{tag}>` 在第 {line} 行开始但未闭合"))
    for tag, line, reason in parser.mismatched:
        problems.append(("必修", f"第 {line} 行 `</{tag}>` {reason}"))
    if not parser.unclosed and not parser.mismatched:
        passed.append("所有标签闭合正常")

    # 7. 标题
    if parser.h1_count == 1:
        passed.append("`h1` 数量为 1")
    elif parser.h1_count == 0:
        problems.append(("建议", "没有 `h1`，页面缺少主标题"))
    else:
        problems.append(("建议", f"`h1` 出现 {parser.h1_count} 次，建议全页只保留一个"))

    levels = [level for level, _ in parser.headings]
    jumps = [(levels[i], levels[i + 1]) for i in range(len(levels) - 1) if levels[i + 1] - levels[i] > 1]
    if jumps and len(levels) > 1:
        problems.append(("建议", f"标题层级跳级 {len(jumps)} 处，例如 {jumps[0][0]} → {jumps[0][1]}"))

    # 8. title
    if parser.title and 5 <= len(parser.title) <= 60:
        passed.append(f"`<title>` 长度合适（{len(parser.title)} 字符）")
    elif not parser.title:
        problems.append(("必修", "缺少 `<title>`"))
    else:
        problems.append(("建议", f"`<title>` 长度 {len(parser.title)} 字符，建议控制在 60 以内"))

    # 9. 内联样式
    if parser.inline_styles:
        preview = "、".join(str(n) for n in parser.inline_styles[:6])
        problems.append(("建议", f"发现 {len(parser.inline_styles)} 处内联 `style`（行 {preview}），建议移到 CSS"))
    else:
        passed.append("没有内联 `style`")

    # 10. CSS 引入
    if re.search(r"\.css[\"']", text):
        passed.append("页面引用了外部样式表")
    else:
        problems.append(("建议", "没有引用外部 `.css`，样式可能写在内联 `<style>` 里"))

    return {
        "path": path,
        "lines": len(text.splitlines()),
        "size": len(text.encode("utf-8")),
        "problems": problems,
        "passed": passed,
    }


def render(results: list[dict]) -> str:
    out: list[str] = []
    hard_total = sum(1 for r in results for level, _ in r["problems"] if level == "必修")
    out.append(f"# 页面体检报告\n")
    out.append(f"共检查 {len(results)} 个文件，硬性必修问题 **{hard_total}** 处。\n")
    for r in results:
        hard = [p for p in r["problems"] if p[0] == "必修"]
        soft = [p for p in r["problems"] if p[0] == "建议"]
        out.append(f"## {r['path'].name}")
        out.append(f"- 路径：`{r['path']}`")
        out.append(f"- 行数 {r['lines']} · 字节 {r['size']}")
        score = max(0, 100 - len(hard) * 8 - len(soft) * 2)
        out.append(f"- 粗估得分：**{score} / 100**（按必修 −8、建议 −2 简单折算）\n")
        if hard:
            out.append("### 必修（会被直接扣分）")
            for i, (_, desc) in enumerate(hard, 1):
                out.append(f"{i}. {desc}")
            out.append("")
        if soft:
            out.append("### 建议修")
            for i, (_, desc) in enumerate(soft, 1):
                out.append(f"{i}. {desc}")
            out.append("")
        if r["passed"]:
            out.append("### 通过项")
            for desc in r["passed"]:
                out.append(f"- {desc}")
            out.append("")
    out.append("---")
    out.append("由 `scripts/check_page.py` 生成，硬性问题之外仍需按 `references/layout-checklist.md` 人工判断布局与对比度。")
    return "\n".join(out)


def collect(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*.html") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="网页作业体检")
    parser.add_argument("target", help="HTML 文件或目录")
    parser.add_argument("--md", metavar="FILE", help="把报告写到文件")
    args = parser.parse_args()

    target = Path(args.target).expanduser()
    if not target.exists():
        print(f"找不到路径：{target}", file=sys.stderr)
        return 2

    files = collect(target)
    if not files:
        print(f"{target} 下没有 .html 文件", file=sys.stderr)
        return 1

    report = render([check_file(f) for f in files])
    if args.md:
        Path(args.md).write_text(report, encoding="utf-8")
        print(f"报告已写入 {args.md}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
