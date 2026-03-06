#!/usr/bin/env python3
"""
005_code_execution.ipynb の response を読みやすく整形して JSON に変換するスクリプト。
file_id を含む完全な content を抽出します（省略なし）。
"""

import json
import re
from pathlib import Path


def extract_matching_brace(s: str, start: int, open_c: str, close_c: str) -> tuple[str, int]:
    """start 位置から始まる括弧の対応する閉じ括弧までを抽出"""
    depth = 0
    i = start
    while i < len(s):
        if s[i] == open_c:
            depth += 1
        elif s[i] == close_c:
            depth -= 1
            if depth == 0:
                return s[start : i + 1], i + 1
        elif s[i] in '"\'' and depth > 0:
            # 文字列内はスキップ
            q = s[i]
            i += 1
            while i < len(s):
                if s[i] == '\\':
                    i += 2
                    continue
                if s[i] == q:
                    break
                i += 1
        i += 1
    return "", start


def parse_content_dict(s: str) -> dict:
    """content= の dict をパース"""
    result = {}
    # type
    if m := re.search(r"'type':\s*'([^']*)'", s):
        result["type"] = m.group(1)
    # stdout
    if "'stdout':" in s:
        m = re.search(r"'stdout':\s*'((?:[^'\\]|\\.)*)'", s)
        if m:
            result["stdout"] = m.group(1).replace("\\n", "\n").replace("\\'", "'")
    # stderr
    if "'stderr':" in s:
        m = re.search(r"'stderr':\s*'((?:[^'\\]|\\.)*)'", s)
        if m:
            result["stderr"] = m.group(1).replace("\\n", "\n").replace("\\'", "'")
    # return_code
    if m := re.search(r"'return_code':\s*(\d+)", s):
        result["return_code"] = int(m.group(1))
    # content array (file_id を含む) - 複数のパターンで抽出
    result["content"] = []
    for m in re.finditer(
        r"\{'type':\s*'bash_code_execution_output',\s*'file_id':\s*'([^']+)'\}",
        s,
    ):
        result["content"].append(
            {"type": "bash_code_execution_output", "file_id": m.group(1)}
        )
    return result


def parse_response(raw: str) -> dict:
    """Message の repr をパースして dict に変換"""
    result = {
        "id": None,
        "model": None,
        "role": None,
        "stop_reason": None,
        "content": [],
        "usage": {},
        "container": {},
    }

    if m := re.search(r"id='(msg_[^']*)'", raw):
        result["id"] = m.group(1)
    if m := re.search(r"model='([^']*)'", raw):
        result["model"] = m.group(1)
    if m := re.search(r"role='([^']*)'", raw):
        result["role"] = m.group(1)
    if m := re.search(r"stop_reason='([^']*)'", raw):
        result["stop_reason"] = m.group(1)

    # usage (cache_creation_input_tokens を避けて、usage=Usage 内の input_tokens を取得)
    usage_match = re.search(r",\s*input_tokens=(\d+)\s*,\s*output_tokens=(\d+)", raw)
    if usage_match:
        result["usage"]["input_tokens"] = int(usage_match.group(1))
        result["usage"]["output_tokens"] = int(usage_match.group(2))
    else:
        if m := re.search(r"input_tokens=(\d+)", raw):
            result["usage"]["input_tokens"] = int(m.group(1))
        if m := re.search(r"output_tokens=(\d+)", raw):
            result["usage"]["output_tokens"] = int(m.group(1))

    # container
    if m := re.search(r"container=\{[^}]*'id':\s*'([^']*)'", raw):
        result["container"]["id"] = m.group(1)
    if m := re.search(r"'expires_at':\s*'([^']*)'", raw):
        result["container"]["expires_at"] = m.group(1)

    # content のパース: ), TextBlock( または ), ServerToolUseBlock( で分割
    # 最初の TextBlock は content=[TextBlock( の直後から始まる
    parts = re.split(r',\s*(TextBlock|ServerToolUseBlock)\(', raw)

    # 最初の TextBlock を抽出（content=[TextBlock( の直後から ), ServerToolUseBlock( の手前まで）
    first_block_start = raw.find("content=[TextBlock(")
    if first_block_start >= 0:
        start = first_block_start + len("content=[TextBlock(")
        end = raw.find("), ServerToolUseBlock(", start)
        if end < 0:
            end = raw.find("), TextBlock(", start)
        if end >= 0:
            block_content = raw[start:end]
            type_m = re.search(r"type='([^']*)'", block_content)
            text_m = re.search(r'text="((?:[^"\\]|\\.)*)"', block_content)
            if text_m or "text=None" in block_content:
                block = {
                    "type": "text",
                    "block_type": type_m.group(1) if type_m else "text",
                    "text": (
                        text_m.group(1).replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
                        if text_m else None
                    ),
                }
                result["content"].append(block)

    i = 1
    while i < len(parts) - 1:
        block_type = parts[i]
        block_content = parts[i + 1] if i + 1 < len(parts) else ""
        i += 2

        if block_type == "TextBlock":
            text_m = re.search(r'text="((?:[^"\\]|\\.)*)"', block_content)
            text_m2 = re.search(r"text=None", block_content)
            type_m = re.search(r"type='([^']*)'", block_content)
            block_type_str = type_m.group(1) if type_m else "text"

            block = {
                "type": "text",
                "block_type": block_type_str,
                "text": None,
            }
            if text_m:
                block["text"] = (
                    text_m.group(1)
                    .replace("\\n", "\n")
                    .replace("\\'", "'")
                    .replace('\\"', '"')
                )
            elif not text_m2:
                block["text"] = ""

            # bash_code_execution_tool_result の場合は content を完全に抽出
            if block_type_str == "bash_code_execution_tool_result" and "content=" in block_content:
                # content={'type': 'bash_code_execution_result', ...} を探す
                content_match = re.search(r"content=\{(?=')", block_content)
                if not content_match:
                    content_match = re.search(r"content=\{\s*'type'", block_content)
                if content_match:
                    start = content_match.start() + len("content=")
                    content_str, _ = extract_matching_brace(
                        block_content, start, "{", "}"
                    )
                    if content_str:
                        block["content"] = parse_content_dict(content_str)

            result["content"].append(block)

        elif block_type == "ServerToolUseBlock":
            id_m = re.search(r"id='([^']*)'", block_content)
            name_m = re.search(r"name='([^']*)'", block_content)
            input_m = re.search(r"input=(\{[^}]+|'[^']*')", block_content)
            cmd = ""
            if input_m:
                inp = input_m.group(1)
                if inp.startswith("{") and "'command'" in inp:
                    cmd_m = re.search(r"'command':\s*'([^']*)'", block_content)
                    if cmd_m:
                        cmd = cmd_m.group(1)
            result["content"].append(
                {
                    "type": "server_tool_use",
                    "id": id_m.group(1) if id_m else None,
                    "name": name_m.group(1) if name_m else None,
                    "command": cmd or None,
                }
            )

    return result


def main():
    base = Path(__file__).parent.parent
    nb_path = base / "005_code_execution.ipynb"
    out_path = base / "documents" / "005_code_execution_output.json"

    with open(nb_path) as f:
        nb = json.load(f)

    raw = None
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if src.strip() in ("response", "response\n"):
            for out in cell.get("outputs", []):
                if "data" in out and "text/plain" in out["data"]:
                    raw = "".join(out["data"]["text/plain"])
                    break
            break

    if not raw:
        raise SystemExit("response の出力が見つかりません")

    data = parse_response(raw)
    data["_meta"] = {
        "source": "005_code_execution.ipynb",
        "note": "file_id を含む完全な content を抽出（省略なし）",
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    file_ids = []
    for block in data["content"]:
        if block.get("content") and isinstance(block["content"], dict):
            for item in block["content"].get("content", []):
                if fid := item.get("file_id"):
                    file_ids.append(fid)

    print(f"✓ 保存完了: {out_path}")
    print(f"  content ブロック数: {len(data['content'])}")
    print(f"  file_id 数: {len(file_ids)}")
    if file_ids:
        print(f"  file_ids: {file_ids}")


if __name__ == "__main__":
    main()
