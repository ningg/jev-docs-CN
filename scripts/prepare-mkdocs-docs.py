#!/usr/bin/env python3
"""Convert documentation/en (Mintlify Markdown) into docs/ for MkDocs Material."""

from __future__ import annotations

import html
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "documentation" / "en"
OUT = ROOT / "docs"
INDEX_TEMPLATE = ROOT / "index-template.md"
STYLES_SRC = ROOT / "stylesheets"
JS_SRC = ROOT / "javascripts"

# Repo-root index-template.md links into documentation/en/; rewrite them
# onto the converted MkDocs paths (including index relocations).
INDEX_TEMPLATE_SRC_PREFIX = "documentation/en/"

# Overview pages that become section indexes for navigation.indexes
INDEX_RELOCATIONS = {
    "primitives.md": "primitives/index.md",
    "patterns.md": "patterns/index.md",
    "cookbooks.md": "cookbooks/index.md",
    "demos.md": "demos/index.md",
    "sdk.md": "sdk/index.md",
    "sdk/python.md": "sdk/python/index.md",
    "sdk/javascript.md": "sdk/javascript/index.md",
}

# Difficulty tags shown in the Cookbooks sidebar (matches docs.typesafe.ai)
COOKBOOK_LEVELS = {
    "cookbooks/consistency_noul_cookbook.md": "Beginner",
    "cookbooks/consistency_choice_cookbook.md": "Beginner",
    "cookbooks/parallel_questions.md": "Beginner",
    "cookbooks/rerank_typesafe.md": "Beginner",
    "cookbooks/semantic_find.md": "Beginner",
    "cookbooks/autoformat.md": "Beginner",
    "cookbooks/function_calling.md": "Intermediate",
    "cookbooks/skill_suggestion.md": "Intermediate",
    "cookbooks/entity_alignment.md": "Beginner",
    "cookbooks/classifying_rag_passages.md": "Intermediate",
    "cookbooks/citation_check.md": "Beginner",
    "cookbooks/llm_guardrails.md": "Intermediate",
    "cookbooks/sde_cascade.md": "Intermediate",
    "cookbooks/date_extraction_cookbook.md": "Beginner",
    "cookbooks/pre_parsed_value_extraction_cookbook.md": "Beginner",
    "cookbooks/hierarchical_classification.md": "Intermediate",
    "cookbooks/autoresearch_feature_discovery.md": "Advanced",
    "cookbooks/classification_using_confidence.md": "Beginner",
}


def final_rel(rel: Path) -> Path:
    return Path(INDEX_RELOCATIONS.get(rel.as_posix(), rel.as_posix()))


def final_dest_md(path_part: str) -> str:
    """Map a site path (with .md) to its final docs-relative location."""
    return INDEX_RELOCATIONS.get(path_part, path_part)


INDEX_BLOCK_RE = re.compile(
    r"^>\s*##\s*Documentation Index\n(?:>.*\n)*\n?",
    re.MULTILINE,
)

MINTLIFY_FOOTER_RE = re.compile(
    r"\n*This documentation is built and hosted on "
    r"(?:\[Mintlify\]\(https://mintlify\.com\)|Mintlify)"
    r", a developer documentation platform\.\s*$",
)

# Opening fences, optionally indented (list nesting / converted Tabs).
FENCE_OPEN_RE = re.compile(
    r"^([ \t]*)```([^\n]*)$",
    re.MULTILINE,
)

ADMONITION_TAGS = {
    "Tip": "tip",
    "Note": "note",
    "Warning": "warning",
    "Info": "info",
    "Check": "success",
}


def find_tag_close(text: str, start: int) -> int:
    """Return index of '>' that closes the opening tag starting at start ('<')."""
    i = start + 1
    in_quote: str | None = None
    while i < len(text):
        ch = text[i]
        if in_quote:
            if ch == in_quote and text[i - 1] != "\\":
                in_quote = None
        elif ch in "\"'":
            in_quote = ch
        elif ch == ">":
            return i
        i += 1
    return -1


def find_matching_close(text: str, open_tag_name: str, open_start: int) -> tuple[int, int] | None:
    """
    Given start of '<Tag...', return (content_start, close_end) where close_end is
    past '</Tag>'. Handles nested same-named tags. Quote-aware for attributes.
    """
    close_gt = find_tag_close(text, open_start)
    if close_gt < 0:
        return None
    open_tag = text[open_start : close_gt + 1]
    if open_tag.endswith("/>"):
        return close_gt + 1, close_gt + 1  # self-closing: no content
    content_start = close_gt + 1
    pattern_open = re.compile(rf"<{open_tag_name}\b")
    pattern_close = re.compile(rf"</{open_tag_name}\s*>")
    pos = content_start
    depth = 1
    while depth > 0 and pos < len(text):
        mo = pattern_open.search(text, pos)
        mc = pattern_close.search(text, pos)
        if mc is None:
            return None
        if mo and mo.start() < mc.start():
            gt = find_tag_close(text, mo.start())
            if gt < 0:
                return None
            nested_open = text[mo.start() : gt + 1]
            # Self-closing nested tags do not increase depth
            if not nested_open.rstrip().endswith("/>"):
                depth += 1
            pos = gt + 1
        else:
            depth -= 1
            if depth == 0:
                return content_start, mc.end()
            pos = mc.end()
    return None


def iter_tags(text: str, tag_name: str):
    """Yield (start, attrs, content_or_none, end) for each top-level tag occurrence."""
    pattern = re.compile(rf"<{tag_name}\b")
    pos = 0
    while True:
        m = pattern.search(text, pos)
        if not m:
            break
        gt = find_tag_close(text, m.start())
        if gt < 0:
            break
        open_tag = text[m.start() : gt + 1]
        attrs = open_tag[len(tag_name) + 1 : -1].strip()
        if attrs.endswith("/"):
            attrs = attrs[:-1].rstrip()
        if open_tag.rstrip().endswith("/>") or open_tag.endswith("/>"):
            yield m.start(), attrs, None, gt + 1
            pos = gt + 1
            continue
        matched = find_matching_close(text, tag_name, m.start())
        if not matched:
            pos = gt + 1
            continue
        content_start, close_end = matched
        if content_start == close_end:
            # self-closing via find_matching_close
            yield m.start(), attrs, None, close_end
            pos = close_end
            continue
        yield m.start(), attrs, text[content_start:close_end - len(f"</{tag_name}>")].rstrip(), close_end
        # Actually content should exclude closing tag - fix:
        # close_end is past </Tag>, content is content_start until start of </Tag>
        pos = close_end


def replace_tags(text: str, tag_name: str, replacer) -> str:
    """Replace all occurrences of tag_name using replacer(attrs, content|None) -> str.
    Processes from the end / repeatedly innermost-first by scanning left-to-right
    but using matching that handles nesting; for nested same tags, process
    innermost by looping until stable.
    """
    for _ in range(50):
        pattern = re.compile(rf"<{tag_name}\b")
        # Find innermost: a tag whose content does not contain another same tag
        candidates = []
        pos = 0
        while True:
            m = pattern.search(text, pos)
            if not m:
                break
            gt = find_tag_close(text, m.start())
            if gt < 0:
                break
            open_tag = text[m.start() : gt + 1]
            attrs_raw = open_tag[len(tag_name) + 1 :]
            self_closing = open_tag.rstrip().endswith("/>")
            if self_closing:
                attrs = attrs_raw[:-2].strip() if attrs_raw.rstrip().endswith("/") else attrs_raw[:-1].strip()
                # normalize
                if attrs.endswith("/"):
                    attrs = attrs[:-1].rstrip()
                attrs = open_tag[len(f"<{tag_name}") : gt].strip()
                if attrs.endswith("/"):
                    attrs = attrs[:-1].rstrip()
                candidates.append((m.start(), gt + 1, attrs, None))
                pos = gt + 1
                continue
            matched = find_matching_close(text, tag_name, m.start())
            if not matched:
                pos = gt + 1
                continue
            content_start, close_end = matched
            # content excludes closing tag
            close_tag = f"</{tag_name}>"
            # find actual close start
            close_start = text.rfind(close_tag, content_start, close_end)
            content = text[content_start:close_start] if close_start >= 0 else text[content_start:close_end]
            attrs = open_tag[len(f"<{tag_name}") : gt].strip()
            candidates.append((m.start(), close_end, attrs, content))
            pos = close_end

        if not candidates:
            break

        # Prefer innermost: content has no nested same tag, or self-closing
        innermost = None
        for start, end, attrs, content in candidates:
            if content is None or not re.search(rf"<{tag_name}\b", content):
                innermost = (start, end, attrs, content)
                break
        if innermost is None:
            # fallback: last candidate (deepest by scan order of nested)
            innermost = candidates[-1]

        start, end, attrs, content = innermost
        replacement = replacer(attrs, content)
        text = text[:start] + replacement + text[end:]
    return text


def attr(attrs: str, name: str) -> str | None:
    m = re.search(rf'{name}="([^"]*)"', attrs)
    if m:
        return html.unescape(m.group(1))
    m = re.search(rf"{name}={{([^}}]+)}}", attrs)
    if m:
        return m.group(1).strip().strip("'\"")
    return None


def indent_block(text: str, prefix: str = "    ") -> str:
    lines = text.strip("\n").split("\n")
    if not lines:
        return prefix
    return "\n".join(prefix + line if line.strip() else prefix.rstrip() for line in lines)


def dedent_block(text: str) -> str:
    """Remove the common leading indent from every non-empty line."""
    lines = text.strip("\n").split("\n")
    nonempty = [ln for ln in lines if ln.strip()]
    if not nonempty:
        return ""
    cut = min(len(ln) - len(ln.lstrip(" \t")) for ln in nonempty)
    out: list[str] = []
    for ln in lines:
        if not ln.strip():
            out.append("")
            continue
        i = 0
        removed = 0
        while i < len(ln) and removed < cut and ln[i] in " \t":
            i += 1
            removed += 1
        out.append(ln[i:])
    return "\n".join(out).strip("\n")


def strip_export_function(text: str, name: str) -> str:
    """Remove ``export function Name(...) { ... }`` blocks from Mintlify MDX.

    The parameter list may contain destructuring ``{...}``, so the first ``{``
    after the name is not always the function body. Match the body brace after
    the closing ``)`` of the parameter list.
    """
    marker = f"export function {name}"
    while True:
        start = text.find(marker)
        if start == -1:
            break
        paren = text.find("(", start + len(marker))
        if paren == -1:
            break
        depth = 0
        i = paren
        while i < len(text):
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        else:
            break
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text) or text[i] != "{":
            break
        depth = 0
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        end = i
        while end < len(text) and text[end] in "\n\r":
            end += 1
        text = text[:start] + text[end:]
    return text


def strip_typesafe_example_helper(text: str) -> str:
    """Remove Mintlify ``export function TypesafeExample(...) { ... }`` helpers."""
    return strip_export_function(text, "TypesafeExample")


def jsx_style_to_html(style_js: str) -> str:
    parts = []
    for m in re.finditer(r"([A-Za-z0-9]+)\s*:\s*['\"]([^'\"]*)['\"]", style_js):
        key = re.sub(r"([a-z])([A-Z])", r"\1-\2", m.group(1)).lower()
        parts.append(f"{key}:{m.group(2)}")
    return ";".join(parts)


def convert_typesafe_examples(text: str) -> str:
    def replacer(attrs: str, content: str | None) -> str:
        # Self-closing with example={{...}} in attrs
        m = re.search(r"example=\{\{([\s\S]*)\}\}\s*$", attrs)
        if m:
            body = m.group(1).strip()
            return f'\n```javascript title="Example request"\n{{\n{body}\n}}\n```\n'
        return (
            '\n!!! note "Example"\n\n'
            "    Interactive example available on the "
            "[official TypeSafe docs](https://docs.typesafe.ai/).\n"
        )

    return replace_tags(text, "TypesafeExample", replacer)


def convert_admonitions(text: str) -> str:
    for tag, kind in ADMONITION_TAGS.items():

        def replacer(attrs: str, content: str | None, kind: str = kind) -> str:
            body = (content or "").strip()
            return f"\n!!! {kind}\n\n{indent_block(body)}\n"

        text = replace_tags(text, tag, replacer)
    return text


def field_heading(attrs: str) -> str:
    name = (
        attr(attrs, "body")
        or attr(attrs, "query")
        or attr(attrs, "path")
        or attr(attrs, "header")
        or attr(attrs, "name")
        or "field"
    )
    typ = attr(attrs, "type") or ""
    required = bool(re.search(r"\brequired\b", attrs))
    bits = []
    if typ:
        bits.append(f"`{html.unescape(typ)}`")
    if required:
        bits.append("required")
    suffix = f" ({', '.join(bits)})" if bits else ""
    return f"**`{name}`**{suffix}"


def convert_param_fields(text: str) -> str:
    def replacer(attrs: str, content: str | None) -> str:
        head = field_heading(attrs)
        if content is None or not content.strip():
            return f"\n{head}\n"
        return f"\n{head}\n\n{content.strip()}\n"

    text = replace_tags(text, "ParamField", replacer)
    text = replace_tags(text, "ResponseField", replacer)
    return text


def convert_expandable(text: str) -> str:
    def replacer(attrs: str, content: str | None) -> str:
        title = attr(attrs, "title") or "Details"
        body = (content or "").strip()
        return f'\n??? note "{title}"\n\n{indent_block(body)}\n'

    return replace_tags(text, "Expandable", replacer)


LUCIDE_ICON_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons"


def convert_accordion(text: str) -> str:
    """Convert Mintlify Accordion/AccordionGroup into TypeSafe-like details blocks."""

    def accordion_replacer(attrs: str, content: str | None) -> str:
        title = attr(attrs, "title") or "Details"
        icon = attr(attrs, "icon") or ""
        body = dedent_block(content or "")
        icon_html = ""
        if icon and re.fullmatch(r"[a-z0-9-]+", icon):
            icon_html = (
                f'<img class="ts-acc-icon" '
                f'src="{LUCIDE_ICON_CDN}/{icon}.svg" alt="" aria-hidden="true" />'
            )
        return (
            f'\n<details class="ts-accordion" markdown="1">\n'
            f"<summary>{icon_html}"
            f'<span class="ts-acc-title">{html.escape(title)}</span></summary>\n\n'
            f"{body}\n\n"
            f"</details>\n"
        )

    text = replace_tags(text, "Accordion", accordion_replacer)

    def group_replacer(attrs: str, content: str | None) -> str:
        inner = (content or "").strip()
        return f'\n<div class="ts-accordion-group" markdown="1">\n\n{inner}\n\n</div>\n'

    text = replace_tags(text, "AccordionGroup", group_replacer)
    return text


def convert_tabs(text: str) -> str:
    """Convert Mintlify <Tabs>/<Tab> into pymdownx.tabbed content tabs."""

    def tabs_replacer(attrs: str, content: str | None) -> str:
        inner = content or ""

        def collect_tabs(src: str) -> list[tuple[str, str]]:
            result = []
            pattern = re.compile(r"<Tab\b")
            pos = 0
            while True:
                m = pattern.search(src, pos)
                if not m:
                    break
                gt = find_tag_close(src, m.start())
                if gt < 0:
                    break
                open_tag = src[m.start() : gt + 1]
                tattrs = open_tag[len("<Tab") : gt].strip()
                matched = find_matching_close(src, "Tab", m.start())
                if not matched:
                    pos = gt + 1
                    continue
                cstart, cend = matched
                close_start = src.rfind("</Tab>", cstart, cend)
                body = src[cstart:close_start] if close_start >= 0 else ""
                title = attr(tattrs, "title") or "Tab"
                result.append((title, body))
                pos = cend
            return result

        parts: list[str] = []
        for title, body in collect_tabs(inner):
            body = dedent_block(body)
            safe_title = title.replace('"', '\\"')
            parts.append(f'=== "{safe_title}"\n\n{indent_block(body)}\n')
        return "\n".join(parts) + "\n" if parts else inner

    # Innermost Tabs first via replace_tags loop
    return replace_tags(text, "Tabs", tabs_replacer)


def convert_steps(text: str) -> str:
    def steps_replacer(attrs: str, content: str | None) -> str:
        inner = content or ""
        parts = []
        n = 1
        pattern = re.compile(r"<Step\b")
        pos = 0
        while True:
            m = pattern.search(inner, pos)
            if not m:
                break
            gt = find_tag_close(inner, m.start())
            if gt < 0:
                break
            open_tag = inner[m.start() : gt + 1]
            sattrs = open_tag[len("<Step") : gt].strip()
            matched = find_matching_close(inner, "Step", m.start())
            if not matched:
                pos = gt + 1
                continue
            cstart, cend = matched
            close_start = inner.rfind("</Step>", cstart, cend)
            body = inner[cstart:close_start].strip() if close_start >= 0 else ""
            title = attr(sattrs, "title") or f"Step {n}"
            parts.append(f"### {n}. {title}\n\n{body}")
            n += 1
            pos = cend
        return "\n\n".join(parts) + "\n" if parts else inner

    return replace_tags(text, "Steps", steps_replacer)


def convert_cards_columns(text: str) -> str:
    text = replace_tags(text, "Columns", lambda attrs, content: "\n" + (content or "") + "\n")

    def card_replacer(attrs: str, content: str | None) -> str:
        title = attr(attrs, "title") or "Card"
        href = attr(attrs, "href")
        body = (content or "").strip()
        if href:
            return f"\n- **[{title}]({href})** — {body}\n"
        return f"\n#### {title}\n\n{body}\n"

    return replace_tags(text, "Card", card_replacer)


def convert_frame(text: str) -> str:
    def replacer(attrs: str, content: str | None) -> str:
        inner = content or ""
        imgs = re.findall(r"<img\b[^>]*>", inner)
        iframes = re.findall(
            r"<iframe\b[^>]*>.*?</iframe>|<iframe\b[^>]*/>",
            inner,
            re.DOTALL,
        )
        chosen: list[str] = []
        if iframes:
            chosen = iframes
        elif imgs:
            light = [i for i in imgs if "dark:hidden" in i or "block dark:hidden" in i]
            chosen = light[:1] if light else imgs[:1]
        out = []
        for tag in chosen:
            tag = re.sub(
                r"style=\{\{([\s\S]*?)\}\}",
                lambda mm: f'style="{jsx_style_to_html(mm.group(1))}"',
                tag,
            )
            tag = re.sub(r'\sclassName="[^"]*"', "", tag)
            tag = re.sub(r'\sdata-path="[^"]*"', "", tag)
            tag = re.sub(r'\swidth="[^"]*"', "", tag)
            tag = re.sub(r'\sheight="[^"]*"', "", tag)
            out.append(tag)
        return "\n" + "\n".join(out) + "\n"

    return replace_tags(text, "Frame", replacer)


def convert_sdk_signature(text: str) -> str:
    def replacer(attrs: str, content: str | None) -> str:
        inner = content or ""

        def link_repl(lm: re.Match[str]) -> str:
            href = lm.group(1)
            label_bits = re.findall(r'\{"([^"]*)"\}', lm.group(2))
            label = "".join(label_bits) if label_bits else href.rsplit("/", 1)[-1]
            return f"[{label}]({href})"

        inner = re.sub(
            r'<a\s+href="([^"]*)"[^>]*>([\s\S]*?)</a>',
            link_repl,
            inner,
        )
        pieces: list[str] = []
        pos = 0
        for sm in re.finditer(r'\{"((?:\\.|[^"\\])*)"\}', inner):
            pieces.append(inner[pos : sm.start()])
            raw = sm.group(1)
            pieces.append(html.unescape(raw))
            pos = sm.end()
        pieces.append(inner[pos:])
        merged = "".join(pieces)
        merged = re.sub(r"<[^>]+>", "", merged)
        merged = merged.replace("\n", "").strip()
        merged = re.sub(r"\s+", " ", merged)
        if not merged:
            return ""
        return f"\n```text\n{merged}\n```\n"

    return replace_tags(text, "SdkSignature", replacer)


def convert_code_group(text: str) -> str:
    return replace_tags(text, "CodeGroup", lambda attrs, content: "\n" + (content or "") + "\n")


def strip_explorers(text: str) -> str:
    for name in (
        "ScoreExplorer",
        "ConfidenceExplorer",
        "ScoreConfidenceExplorer",
    ):
        text = strip_export_function(text, name)
        text = re.sub(
            rf"<{name}\s*/>",
            f'\n!!! note "Interactive widget"\n\n'
            f"    The interactive {name} is available on the "
            f"[official TypeSafe docs](https://docs.typesafe.ai/).\n",
            text,
        )
    return text


def clean_fences(text: str) -> str:
    """Normalize Mintlify fence meta for MkDocs Material.

    Keeps ``title="..."`` (and bare titles like ``json Example request``) so
    Material can render the code-block header; strips theme/focus/etc.
    """

    def repl(m: re.Match[str]) -> str:
        indent, meta = m.group(1), (m.group(2) or "").strip()
        if not meta:
            return f"{indent}```"

        title: str | None = None
        title_m = re.search(r"""\btitle=(["'])(.*?)\1""", meta)
        if title_m:
            title = title_m.group(2)

        rest = meta
        rest = re.sub(r"""\btitle=(["'])(.*?)\1""", "", rest)
        rest = re.sub(r"\btheme=\{[^}]*\}", "", rest)
        rest = re.sub(r"\bfocus=\{[^}]*\}", "", rest)
        rest = re.sub(r"\bactions=\{[^}]*\}", "", rest)
        rest = re.sub(r"\bexpandable\b", "", rest)
        rest = re.sub(r"\bwrap\b", "", rest)
        rest = rest.strip().lstrip("`").strip()

        parts = rest.split()
        lang = parts[0] if parts else ""
        if title is None and len(parts) > 1:
            title = " ".join(parts[1:])

        out = f"{indent}```{lang}"
        if title:
            # Escape quotes in title for the attribute form Material expects.
            safe = title.replace('"', '\\"')
            out += f' title="{safe}"'
        return out

    return FENCE_OPEN_RE.sub(repl, text)


ORDERED_ITEM_RE = re.compile(r"^(\d+)\.\s")
# ## / ### break a list; ####+ (e.g. converted Tabs) may nest under the prior item.
SECTION_HEADING_RE = re.compile(r"^#{1,3}\s")


def continue_ordered_lists(text: str) -> str:
    """Nest blocks that interrupt an ordered list so numbering stays continuous.

    A column-0 fence (or other content) between ``2.`` and ``3.`` makes
    Python-Markdown start a new ``<ol>`` at 1. Indenting that content under
    the previous item keeps a single list.
    """
    lines = text.split("\n")
    result: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if not ORDERED_ITEM_RE.match(line):
            result.append(line)
            i += 1
            continue

        # Ordered-list run: keep nesting interrupters until a real break.
        result.append(line)
        i += 1
        while i < n:
            while i < n and (lines[i].startswith(("    ", "\t"))):
                result.append(lines[i])
                i += 1

            blank_start = i
            while i < n and lines[i].strip() == "":
                i += 1

            if i >= n:
                result.extend(lines[blank_start:i])
                break

            if SECTION_HEADING_RE.match(lines[i]):
                result.extend(lines[blank_start:i])
                break

            if ORDERED_ITEM_RE.match(lines[i]):
                result.append("")
                result.append(lines[i])
                i += 1
                continue

            block_start = i
            while i < n:
                if SECTION_HEADING_RE.match(lines[i]):
                    break
                if ORDERED_ITEM_RE.match(lines[i]):
                    break
                i += 1

            nxt = ORDERED_ITEM_RE.match(lines[i]) if i < n else None
            if nxt and int(nxt.group(1)) > 1:
                result.append("")
                for j in range(block_start, i):
                    if lines[j].strip() == "":
                        result.append("")
                    else:
                        # Always nest one list level. Do not skip lines that
                        # already have 4 spaces — that is often code indent
                        # (e.g. JSON), not list nesting.
                        result.append("    " + lines[j])
                continue

            result.extend(lines[blank_start:i])
            break

    return "\n".join(result)


def fix_links(text: str, rel_path: Path) -> str:
    def rel_target(target: str) -> str:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return target
        path_part, frag = (target.split("#", 1) + [""])[:2]
        path_part = path_part.lstrip("/")
        if not path_part:
            return "#" + frag if frag else target
        if not path_part.endswith(".md"):
            path_part = path_part + ".md"
        dest = Path(final_dest_md(path_part))
        start_dir = rel_path.parent
        rel = Path(os.path.relpath(dest.as_posix(), start=start_dir.as_posix() or "."))
        out = rel.as_posix()
        if frag:
            out += "#" + frag
        return out

    def md_link(m: re.Match[str]) -> str:
        label, href = m.group(1), m.group(2)
        if href.startswith("/") and not href.startswith("//"):
            return f"[{label}]({rel_target(href)})"
        return m.group(0)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", md_link, text)

    def href_attr(m: re.Match[str]) -> str:
        href = m.group(1)
        if href.startswith("/") and not href.startswith("//"):
            return f'href="{rel_target(href)}"'
        return m.group(0)

    text = re.sub(r'href="([^"]+)"', href_attr, text)
    return text


def strip_residual_jsx(text: str) -> str:
    text = re.sub(r"</?(?:CodeBlock)[^>]*>", "", text)
    text = re.sub(r"\{/\*[\s\S]*?\*/\}", "", text)
    # Leftover Tab wrappers if any
    text = re.sub(r"</?Tab\b[^>]*>", "", text)
    text = re.sub(r"</?Tabs\b[^>]*>", "", text)
    return text


def inject_level_front_matter(text: str, rel_path: Path) -> str:
    """Add `level:` front matter for cookbook pages (sidebar difficulty tags)."""
    level = COOKBOOK_LEVELS.get(rel_path.as_posix())
    if not level:
        return text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = text[4:end]
            if re.search(r"(?m)^level:\s*", fm):
                fm = re.sub(r"(?m)^level:\s*.*$", f"level: {level}", fm)
            else:
                fm = fm.rstrip() + f"\nlevel: {level}\n"
            return f"---\n{fm}\n---\n" + text[end + 5 :]
    return f"---\nlevel: {level}\n---\n\n{text}"


def strip_mintlify_footer(text: str) -> str:
    """Remove the Mintlify hosting blurb that Mintlify appends to every page."""
    return MINTLIFY_FOOTER_RE.sub("", text)


def finalize_trailing_blank_lines(text: str, blank_lines: int = 4) -> str:
    """Ensure the file ends with exactly ``blank_lines`` empty lines after content."""
    return text.rstrip() + ("\n" * (blank_lines + 1))


def transform(text: str, rel_path: Path) -> str:
    text = INDEX_BLOCK_RE.sub("", text)
    text = strip_typesafe_example_helper(text)
    # Nested structures: convert children before parents where needed
    text = convert_typesafe_examples(text)
    text = convert_param_fields(text)
    text = convert_expandable(text)
    text = convert_param_fields(text)  # nested fields inside expandables
    text = convert_accordion(text)
    text = convert_tabs(text)
    text = convert_steps(text)
    text = convert_admonitions(text)
    text = convert_cards_columns(text)
    text = convert_frame(text)
    text = convert_sdk_signature(text)
    text = convert_code_group(text)
    text = strip_explorers(text)
    text = clean_fences(text)
    text = fix_links(text, rel_path)
    text = strip_residual_jsx(text)
    text = continue_ordered_lists(text)
    text = strip_mintlify_footer(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = inject_level_front_matter(text, rel_path)
    return finalize_trailing_blank_lines(text, blank_lines=4)


def rewrite_index_template_links(text: str) -> str:
    """Map repo-root template links onto generated docs/ paths."""

    def repl(m: re.Match[str]) -> str:
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        path_part, frag = (href.split("#", 1) + [""])[:2]
        path_part = path_part.lstrip("./")
        if path_part.startswith(INDEX_TEMPLATE_SRC_PREFIX):
            path_part = path_part[len(INDEX_TEMPLATE_SRC_PREFIX) :]
        if path_part.endswith(".md"):
            path_part = final_dest_md(path_part)
        out = path_part
        if frag:
            out += "#" + frag
        return f"[{label}]({out})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)


def write_index() -> None:
    if not INDEX_TEMPLATE.is_file():
        raise SystemExit(f"Missing index template: {INDEX_TEMPLATE}")
    text = rewrite_index_template_links(INDEX_TEMPLATE.read_text(encoding="utf-8"))
    (OUT / "index.md").write_text(
        finalize_trailing_blank_lines(text),
        encoding="utf-8",
    )


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Missing source directory: {SRC}")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    count = 0
    for src_file in sorted(SRC.rglob("*.md")):
        rel = src_file.relative_to(SRC)
        out_rel = final_rel(rel)
        dest = OUT / out_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = src_file.read_text(encoding="utf-8")
        dest.write_text(transform(raw, out_rel), encoding="utf-8")
        count += 1

    write_index()

    # Copy theme assets that live outside the wiped docs/ tree
    if STYLES_SRC.is_dir():
        styles_dest = OUT / "stylesheets"
        styles_dest.mkdir(parents=True, exist_ok=True)
        for css in STYLES_SRC.glob("*.css"):
            shutil.copy2(css, styles_dest / css.name)
        print(f"Copied stylesheets → {styles_dest}")

    if JS_SRC.is_dir():
        js_dest = OUT / "javascripts"
        js_dest.mkdir(parents=True, exist_ok=True)
        for js in JS_SRC.glob("*.js"):
            shutil.copy2(js, js_dest / js.name)
        print(f"Copied javascripts → {js_dest}")

    print(f"Prepared {count} pages + index.md → {OUT}")


if __name__ == "__main__":
    main()
