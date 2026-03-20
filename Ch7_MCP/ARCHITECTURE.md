# Ch7_MCP アーキテクチャ解説

## 概要

このプロジェクトは **MCP（Model Context Protocol）** を使って Claude と外部ツール・リソース・プロンプトを連携させる CLI チャットアプリケーションです。

```
ユーザー入力
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  main.py  (エントリポイント)                         │
│    │                                                 │
│    ├── MCPClient × N  ─────────── MCP サーバー群     │
│    │     └── mcp_server.py (DocumentMCP)             │
│    │                                                 │
│    ├── Claude (core/claude.py)                       │
│    │                                                 │
│    └── CliChat (core/cli_chat.py)                    │
│          ├── Chat (core/chat.py)  ←── 基底クラス     │
│          └── ToolManager (core/tools.py)             │
│                                                      │
│    CliApp (core/cli.py)  ←── UI レイヤー             │
└─────────────────────────────────────────────────────┘
```

---

## ファイル別解説

### [main.py](main.py) — エントリポイント

アプリ全体の初期化と起動を担います。

```python
async def main():
    claude_service = Claude(model=claude_model)  # ① Claude サービス生成

    # ② MCPClient を AsyncExitStack で管理（確実にクリーンアップ）
    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)   # DocumentMCP サーバーへ接続
        )
        # コマンドライン引数で追加サーバーを動的に登録
        for i, server_script in enumerate(server_scripts):
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        chat = CliChat(doc_client=doc_client, clients=clients, ...)
        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()
```

**ポイント：**
- `AsyncExitStack` を使うことで、複数の MCP クライアント接続を一括でライフサイクル管理
- `doc_client`（DocumentMCP 専用）と汎用 `clients` を分けて管理
- `USE_UV=1` 環境変数で `uv run` と `python` を切り替え可能

---

### [mcp_server.py](mcp_server.py) — MCP サーバー

`FastMCP` を使ってドキュメント操作機能を提供する MCP サーバー（スタブ）。

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "...",
    "report.pdf":    "...",
    # ...
}

# ← TODO: ツール・リソース・プロンプトを実装予定
```

**実装予定の機能（TODO）：**

| 種別 | 内容 |
|------|------|
| Tool | ドキュメントの読み取り (`read_doc`) |
| Tool | ドキュメントの編集 (`edit_doc`) |
| Resource | 全ドキュメント ID 一覧 (`docs://documents`) |
| Resource | 特定ドキュメントの内容 (`docs://documents/{id}`) |
| Prompt | Markdown 形式への変換 |
| Prompt | ドキュメント要約 |

サーバーは `stdio` トランスポートで動作し、クライアントと標準入出力経由で通信します。

---

### [mcp_client.py](mcp_client.py) — MCP クライアント

MCP サーバーへの接続・通信を担うクラス。非同期コンテキストマネージャとして設計されています。

```
MCPClient
  ├── connect()          サーバープロセスを起動し stdio_client で接続
  ├── session()          ClientSession を返す（未接続時は例外）
  ├── list_tools()       ← TODO: サーバーのツール一覧取得
  ├── call_tool()        ← TODO: ツール呼び出し
  ├── list_prompts()     ← TODO: プロンプト一覧取得
  ├── get_prompt()       ← TODO: プロンプト取得
  ├── read_resource()    ← TODO: リソース読み取り
  └── cleanup()          接続をクリーンアップ
```

接続は `StdioServerParameters` でサーバーのコマンドを指定し、`stdio_client` を経由して `ClientSession` を確立します。

---

### [core/claude.py](core/claude.py) — Claude API ラッパー

Anthropic SDK を薄くラップしたサービスクラス。

```
Claude
  ├── add_user_message()      メッセージリストにユーザーターンを追加
  ├── add_assistant_message() メッセージリストにアシスタントターンを追加
  ├── text_from_message()     レスポンスからテキストブロックだけ抽出
  └── chat()                  messages.create() を呼び出してレスポンス返却
```

`chat()` の主要パラメータ：

| パラメータ | 説明 |
|------------|------|
| `tools` | MCP から取得したツール定義を渡す |
| `thinking` | 拡張思考モードの有効化 |
| `thinking_budget` | 思考トークン上限（デフォルト 1024） |
| `stop_sequences` | 停止シーケンス |

---

### [core/chat.py](core/chat.py) — チャット基底クラス

エージェントループの中核ロジックを持つ基底クラス。

```python
async def run(self, query: str) -> str:
    await self._process_query(query)   # メッセージを準備

    while True:
        response = self.claude_service.chat(
            messages=self.messages,
            tools=await ToolManager.get_all_tools(self.clients),
        )
        self.claude_service.add_assistant_message(self.messages, response)

        if response.stop_reason == "tool_use":
            # ツール呼び出しが必要な場合はツールを実行してループ継続
            tool_result_parts = await ToolManager.execute_tool_requests(...)
            self.claude_service.add_user_message(self.messages, tool_result_parts)
        else:
            # 最終テキスト応答が得られたらループ終了
            return self.claude_service.text_from_message(response)
```

**エージェントループの流れ：**

```
query 入力
  → Claude に送信（ツール定義付き）
  → stop_reason == "tool_use" ?
       YES → ツール実行 → 結果をメッセージに追加 → ループ
       NO  → テキスト応答を返す
```

---

### [core/cli_chat.py](core/cli_chat.py) — CLI 特化チャット

`Chat` を継承し、CLI 向けの機能を追加したクラス。

#### 主な追加機能

**1. `@mention` によるリソース埋め込み**

```
ユーザー: "@report.pdf の概要を教えて"
           ↓
_extract_resources() が "@report.pdf" を検出
           ↓
doc_client.read_resource("docs://documents/report.pdf") でコンテンツ取得
           ↓
<document id="report.pdf">...</document> としてプロンプトに埋め込み
```

**2. `/command` によるプロンプト実行**

```
ユーザー: "/summarize report.pdf"
           ↓
_process_command() が "/" で始まることを検出
           ↓
doc_client.get_prompt("summarize", {"doc_id": "report.pdf"}) でプロンプト取得
           ↓
MCP プロンプトをメッセージリストに変換して追加
```

**3. MCP PromptMessage → Anthropic MessageParam 変換**

```
convert_prompt_messages_to_message_params()
  ↓
MCP の PromptMessage (role + TextContent)
  →  Anthropic の MessageParam {"role": ..., "content": ...}
```

---

### [core/tools.py](core/tools.py) — ツール管理

全 MCP クライアントにわたるツール操作を一元管理するクラス。

```
ToolManager (クラスメソッドのみ)
  ├── get_all_tools(clients)
  │     全クライアントから list_tools() を呼び出し、Anthropic 形式に変換
  │     { name, description, input_schema }
  │
  ├── _find_client_with_tool(clients, tool_name)
  │     ツール名を持つクライアントを検索（最初にヒットしたものを返す）
  │
  └── execute_tool_requests(clients, message)
        message 内の tool_use ブロックをすべて処理
          ├── ツールを持つクライアントを検索
          ├── client.call_tool() を呼び出し
          └── ToolResultBlockParam を生成して返す
```

---

### [core/cli.py](core/cli.py) — CLI UI

`prompt_toolkit` を使ったリッチな CLI インターフェース。

#### 主要コンポーネント

**`CommandAutoSuggest`**
- `/` で始まる入力に対して、コマンドの引数名をグレーでサジェスト
- 例：`/summarize` と入力すると ` doc_id` がサジェスト表示

**`UnifiedCompleter`**
- `@` キーでリソース ID（ドキュメント名）をタブ補完
- `/` キーでコマンド名（プロンプト名）をタブ補完
- コマンド後スペースでドキュメント ID をタブ補完

**`CliApp`**

```python
async def initialize(self):
    await self.refresh_resources()   # MCP からドキュメント ID を取得
    await self.refresh_prompts()     # MCP からプロンプト一覧を取得

async def run(self):
    while True:
        user_input = await self.session.prompt_async("> ")
        response = await self.agent.run(user_input)
        print(f"\nResponse:\n{response}")
```

キーバインド：

| キー | 動作 |
|------|------|
| `/` | コマンド補完を起動（バッファ先頭のみ） |
| `@` | リソース補完を起動 |
| `Space` | `/command ` 入力後にドキュメント補完を起動 |

---

## データフロー全体図

```
ユーザー入力: "/summarize @report.pdf の内容は？"
        │
        ▼
  CliApp.run()
        │
        ▼
  CliChat.run(query)
        │
        ├─ _process_command() → "/" 検出 → MCP プロンプト取得
        │       または
        └─ _extract_resources() → "@" 検出 → リソース内容を埋め込み
                │
                ▼
          Chat.run() ─── エージェントループ
                │
                ├── Claude.chat(messages, tools)
                │         │
                │         ▼
                │    [Anthropic API]
                │         │
                │    stop_reason == "tool_use"?
                │         │ YES
                │         ▼
                │    ToolManager.execute_tool_requests()
                │         │
                │         ▼
                │    MCPClient.call_tool()
                │         │
                │         ▼
                │    [MCP Server: mcp_server.py]
                │         │
                └── (結果をメッセージに追加してループ)
                          │ NO (end_turn)
                          ▼
                    テキスト応答を表示
```

---

## 未実装部分（TODO）

現在の実装はスタブ状態です。以下が実装対象：

| ファイル | TODO |
|----------|------|
| `mcp_client.py` | `list_tools()`, `call_tool()`, `list_prompts()`, `get_prompt()`, `read_resource()` |
| `mcp_server.py` | ドキュメント操作ツール、リソース定義、プロンプト定義 |
