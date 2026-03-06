# コード実行の分析結果をダウンロードする方法

## 概要

コード実行ツールで `$OUTPUT_DIR` に保存されたファイル（PNG、TXT、CSV など）は、**Files API** を使ってダウンロードできます。

## ダウンロードの流れ

1. **レスポンスから `file_id` を取得**  
   `response.content` 内の `bash_code_execution_tool_result` ブロックに、生成されたファイルの `file_id` が含まれます。

2. **Files API でダウンロード**  
   `client.beta.files.download(file_id)` でファイルを取得し、`write_to_file()` で保存します。

## 必要な設定

- `anthropic-beta` ヘッダーに `files-api-2025-04-14` を含める（ノートブックでは既に設定済み）

## 実装例

### 1. `file_id` を抽出する関数

```python
def extract_file_ids(response):
    """レスポンスから生成されたファイルの file_id を抽出"""
    file_ids = []
    for item in response.content:
        if getattr(item, "type", None) == "bash_code_execution_tool_result":
            content_item = getattr(item, "content", None)
            if content_item is not None:
                content_type = getattr(content_item, "type", None)
                content_list = getattr(content_item, "content", None) or []
                if content_type == "bash_code_execution_result" and content_list:
                    for file in content_list:
                        file_id = getattr(file, "file_id", None)
                        if file_id:
                            file_ids.append(file_id)
    return file_ids
```

### 2. 全ファイルをダウンロード

```python
# response は chat() の戻り値
for file_id in extract_file_ids(response):
    try:
        file_metadata = get_metadata(file_id)
        download_file(file_id, filename=f"./documents/{file_metadata.filename}")
        print(f"✓ ダウンロード完了: {file_metadata.filename}")
    except Exception as e:
        print(f"✗ {file_id} のダウンロードに失敗: {e}")
```

### 3. ノートブックでの実行例

```python
# チャット実行後
response = chat(messages, tools=[{"type": "code_execution_20250825", "name": "code_execution"}])

# 生成されたファイルを一括ダウンロード
for file_id in extract_file_ids(response):
    download_file(file_id, filename=f"./documents/{get_metadata(file_id).filename}")
```

## 分析で生成されるファイル

今回のチャーン分析では、次の 3 ファイルが `OUTPUT_DIR` に保存されます：

| ファイル名 | 内容 |
|-----------|------|
| `churn_analysis_detailed.png` | 10 個のサブプロットを含む可視化 |
| `churn_analysis_executive_summary.txt` | エグゼクティブサマリーレポート |
| `churn_drivers_statistical_summary.csv` | 統計サマリーテーブル |

## 注意事項

### コンテナの有効期限

コード実行は一時的なコンテナ内で行われ、**有効期限**があります。

- `container.expires_at` で確認可能（例: `2026-03-06T22:33:31Z`）
- 期限を過ぎると、そのコンテナ内のファイルはダウンロードできなくなる可能性があります
- 分析結果を残したい場合は、**実行直後にダウンロード**することを推奨します

### 既知の file_id で個別ダウンロード

レスポンスから取得した `file_id` が分かっている場合は、次のように個別ダウンロードできます：

```python
download_file("file_011CYnYMdAnfTZGCp1q3s14E")  # PNG など
```

※ `file_id` は実行ごとに変わります。新しい実行では `extract_file_ids()` で取得した ID を使用してください。

## 参考

- [Code execution tool - Anthropic Docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool)
- [Files API - Anthropic Docs](https://docs.anthropic.com/en/docs/build-with-claude/files)
