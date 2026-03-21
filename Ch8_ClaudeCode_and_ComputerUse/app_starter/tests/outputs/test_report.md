# テストレポート — `tools/document.py`

**日付:** 2026-03-21
**実行:** pytest 8.3.5
**Python:** 3.13.7
**結果:** 11 件成功、0 件失敗

---

## 概要

| 合計 | 成功 | 失敗 |
|------|------|------|
| 11   | 11   | 0    |

---

## TestBinaryDocumentToMarkdown

`binary_document_to_markdown(binary_data: bytes, file_type: str) -> str` のテスト。

| # | テスト | ステータス | 説明 |
|---|--------|------------|------|
| 1 | `test_fixture_files_exist` | PASSED | フィクスチャ `mcp_docs.docx` と `mcp_docs.pdf` がディスク上に存在することを検証 |
| 2 | `test_binary_document_to_markdown_with_docx` | PASSED | DOCX をバイト列として読み込み Markdown に変換。空でない `str` で、Markdown 用の文字（`#`、`-`、`*` のいずれか）を含むことをアサート |

---

## TestDocumentPathToMarkdown

`document_path_to_markdown(file_path: str) -> str` のテスト。

| # | テスト | ステータス | 説明 |
|---|--------|------------|------|
| 3 | `test_document_path_to_markdown_with_docx` | PASSED | DOCX フィクスチャのパスを渡す。空でない `str` で Markdown 用の文字を含むことをアサート |
| 4 | `test_document_path_to_markdown_with_pdf` | PASSED | PDF フィクスチャのパスを渡す。空でない `str` で Markdown 用の文字を含むことをアサート |
| 5 | `test_binary_document_to_markdown_with_pdf` | PASSED | PDF をバイト列として読み込み Markdown に変換。空でない `str` で Markdown 用の文字を含むことをアサート |
| 6 | `test_file_not_found` | PASSED | 存在しないパスを渡し、`FileNotFoundError` が送出されることをアサート |
| 7 | `test_unsupported_extension` | PASSED | 一時的な `.xyz` ファイルのパスを渡し、結果が `str` であることをアサート（markitdown は未知の拡張子でも例外を出さない） |
| 8 | `test_path_with_spaces` | PASSED | DOCX フィクスチャをスペースを含むパスにコピーし、空でない `str` が返ることをアサート |
| 9 | `test_docx_contains_markdown_headings` | PASSED | DOCX の出力に `#` の見出し構文が含まれることをアサート |
| 10 | `test_pdf_returns_string` | PASSED | PDF の結果が `str` であり、`bytes` や `None` でないことをアサート |
| 11 | `test_docx_returns_string` | PASSED | DOCX の結果が `str` であり、`bytes` や `None` でないことをアサート |

---

## 注記

- テスト 5（`test_binary_document_to_markdown_with_pdf`）は `TestDocumentPathToMarkdown` 内に置かれているが、下位の `binary_document_to_markdown` を直接検証している。
- テスト 7（`test_unsupported_extension`）は、`markitdown` が未知のファイル拡張子に対してエラーを出さずに処理することを記録している。関数の docstring では呼び出し側に未対応形式を使わないよう促しているが、実行時にそれを強制する仕組みはない。
