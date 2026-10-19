"""MkDocs hook: render Mintlify ``<TypesafeExample>`` tags.

Loaded from ``mkdocs.yml`` ``hooks``. Generated ``docs/`` pages keep the tag.
``on_page_markdown`` turns each tag into a fenced code block (``theme`` is
``display``, the body is ``example``) plus a placeholder the playground script
fills in.
"""

from __future__ import annotations

import base64
import html
import re


def _find_tag_close(text: str, start: int) -> int:
    """Index of the ``>`` that closes the tag starting at ``start``."""
    i = start + 1
    in_quote: str | None = None
    while i < len(text):
        ch = text[i]
        if in_quote:
            if ch == "\\":
                i += 2
                continue
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'`":
            in_quote = ch
        elif ch == ">":
            return i
        i += 1
    return -1


def _attr(attrs: str, name: str) -> str | None:
    match = re.search(rf'{name}="([^"]*)"', attrs)
    if match:
        return html.unescape(match.group(1))
    match = re.search(rf"{name}={{([^}}]+)}}", attrs)
    if match:
        return match.group(1).strip().strip("'\"")
    return None


def _extract_jsx_expr(attrs: str, name: str) -> str | None:
    """Return the brace-delimited JSX expression after ``name=``."""
    match = re.search(rf"\b{name}\s*=\s*\{{", attrs)
    if not match:
        return None
    start = match.end() - 1
    depth = 0
    i = start
    in_quote: str | None = None
    while i < len(attrs):
        ch = attrs[i]
        if in_quote:
            if ch == "\\":
                i += 2
                continue
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'`":
            in_quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return attrs[start : i + 1]
        i += 1
    return None


def _dedent(text: str) -> str:
    lines = text.strip("\n").split("\n")
    nonempty = [line for line in lines if line.strip()]
    if not nonempty:
        return ""
    cut = min(len(line) - len(line.lstrip(" \t")) for line in nonempty)
    out: list[str] = []
    for line in lines:
        if not line.strip():
            out.append("")
            continue
        i = 0
        removed = 0
        while i < len(line) and removed < cut and line[i] in " \t":
            i += 1
            removed += 1
        out.append(line[i:])
    return "\n".join(out).strip("\n")


def example_source(attrs: str) -> str | None:
    """JS object literal stored in ``example={{ ... }}``."""
    expr = _extract_jsx_expr(attrs, "example")
    if not expr or len(expr) < 2:
        return None
    body = _dedent(expr[1:-1].strip())
    if body.startswith("{") and body.endswith("}") and "\n" in body:
        inner = _dedent(body[1:-1])
        body = "{\n" + inner + "\n}" if inner else "{}"
    return body


def render_typesafe_example(attrs: str, indent: str) -> str | None:
    """Fence plus playground placeholder. ``indent`` is prepended to follow-on lines."""
    body = example_source(attrs)
    if not body:
        return None
    display = _attr(attrs, "display")
    title = _attr(attrs, "title")
    bits = [".javascript"]
    if display:
        bits.append(f'theme="{display.replace(chr(34), r"\"")}"')
    if title:
        bits.append(f'title="{title.replace(chr(34), r"\"")}"')
    header = "{" + " ".join(bits) + "}"
    payload = base64.b64encode(body.encode("utf-8")).decode("ascii")
    # Opening fence keeps the indent already sitting before the tag.
    lines = [f"```{header}"]
    lines.extend((indent + line) if line else indent for line in body.split("\n"))
    lines.append(f"{indent}```")
    lines.append("")
    lines.append(f'{indent}<div class="ts-playground" data-ts-example="{payload}">')
    lines.append(
        f'{indent}<a class="ts-playground-link" href="#" target="_blank" rel="noopener noreferrer">'
        "Try it in the Playground →</a>"
    )
    lines.append(f"{indent}</div>")
    return "\n".join(lines) + "\n"


def replace_typesafe_examples(text: str) -> str:
    pattern = re.compile(r"<TypesafeExample\b")
    pos = 0
    chunks: list[str] = []
    while True:
        match = pattern.search(text, pos)
        if not match:
            chunks.append(text[pos:])
            break
        gt = _find_tag_close(text, match.start())
        if gt < 0:
            chunks.append(text[pos:])
            break
        open_tag = text[match.start() : gt + 1]
        if not open_tag.rstrip().endswith("/>"):
            pos = gt + 1
            continue
        line_start = text.rfind("\n", 0, match.start()) + 1
        raw_indent = text[line_start:match.start()]
        indent = raw_indent if raw_indent.strip() == "" else ""
        attrs = open_tag[len("<TypesafeExample") : -1].strip()
        if attrs.endswith("/"):
            attrs = attrs[:-1].rstrip()
        rendered = render_typesafe_example(attrs, indent)
        if rendered is None:
            pos = gt + 1
            continue
        chunks.append(text[pos:match.start()])
        chunks.append(rendered)
        pos = gt + 1
    return "".join(chunks)


def on_page_markdown(markdown: str, **kwargs) -> str:
    if "<TypesafeExample" not in markdown:
        return markdown
    return replace_typesafe_examples(markdown)
