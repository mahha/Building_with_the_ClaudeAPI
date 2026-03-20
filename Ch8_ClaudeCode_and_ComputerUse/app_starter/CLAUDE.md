# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run MCP server
uv run main.py

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_docx
```

## Architecture

This package exposes document-processing tools via an MCP server using the **FastMCP** framework.

- `main.py` — creates a `FastMCP("docs")` instance and registers tools with `mcp.tool()(function)`, then calls `mcp.run()` (stdio transport)
- `tools/` — each file contains plain Python functions; they are imported and registered in `main.py`
- `tests/` — pytest tests using real fixture files in `tests/fixtures/` (no mocking)

## Defining MCP Tools

Tools are plain Python functions registered with the MCP server:

```python
# main.py
from tools.my_module import my_function
mcp.tool()(my_function)
```

Tool docstrings and parameter descriptions form the schema exposed to AI assistants. Follow this pattern:

```python
from pydantic import Field

def my_tool(
    param1: str = Field(description="Detailed description of this parameter"),
    param2: int = Field(description="Explain what this parameter does"),
) -> ReturnType:
    """One-line summary.

    Detailed explanation of functionality.

    When to use (and when not to use) this tool.

    Examples:
        Input: ...
        Output: ...
    """
    # implementation
```

- Always apply appropriate type annotations to all function arguments and return values
- Use `Field` from pydantic for all parameter descriptions — these appear in the tool schema
- Docstrings must include: summary, detailed explanation, usage guidance, and examples

## Document Conversion

`tools/document.py` provides `binary_document_to_markdown(binary_data: bytes, file_type: str) -> str` using the `markitdown` library. It accepts raw bytes and a file extension (e.g. `".docx"`, `".pdf"`). This tool is defined but **not yet registered** in `main.py`.
