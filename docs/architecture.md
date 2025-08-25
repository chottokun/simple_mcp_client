# 2. アーキテクチャ (Architecture)

このドキュメントでは、インテリジェントRAGチャットシステムの技術的な構造と設計について詳細に解説します。

## 2.1. システム構成図

システムは、主に「Frontend」「Backend」「Tool Services」の3つのレイヤーで構成されています。

```mermaid
graph TD
    subgraph Browser
        A[Streamlit UI]
    end

    subgraph "Backend Server (Docker)"
        B[FastAPI: Chat API]
        C[LangChain: Agent/Orchestrator]
        D[FastAPI: Tool Server]
        E[Tool: ingest_document]
        F[Tool: search_data]
        BR[Tool: browse_website]
    end

    subgraph "Tool Services (Docker / External)"
        G[Vector Store: ChromaDB]
        H[LLM Service: Ollama]
        PW[Playwright MCP Server]
        GH[GitHub MCP Server]
    end

    A -- "1. /api/chat (HTTP)" --> B
    B -- "2. invoke(question)" --> C
    C -- "3. Decide which tool to use" --> D & BR & GH

    subgraph "Internal Search Flow"
        D -- "Calls" --> F
        F -- "query" --> G
        G -- "results" --> F
        F -- "JSON" --> D
        D -- "observation" --> C
    end

    subgraph "GitHub Search Flow"
        C -- "Calls" --> GH
        GH -- "observation" --> C
    end

    subgraph "Website Browsing Flow"
        C -- "Calls" --> PW
        PW -- "observation" --> C
    end

    C -- "4. Generate final prompt" --> H
    H -- "5. Return final answer (JSON)" --> C
    C -- "6. Return structured answer" --> B
    B -- "7. Return final response" --> A

    subgraph "Ingestion Flow (CLI)"
        I[CLI: cli.py]
        J[File (.pdf, .md, etc.)]
    end

    J -- "a. Read file" --> I
    I -- "b. /tools/ingest (HTTP)" --> D
    E -- "c. Create embeddings" --> H
    E -- "d. Write to vector store" --> G
```

## 2.2. コンポーネント詳細

### Frontend
-   **Streamlit UI (`streamlit_app.py`)**: ユーザーが直接操作するWebインターフェースです。

### Backend
-   **FastAPI: Chat API (`app/main.py`)**: ユーザーからのリクエストを受け付けるメインのAPIサーバーです。
-   **FastAPI: Tool Server (`app/tool_router.py`)**: `local_document_search`ツールが使用する、`ingest`と`search`の内部APIエンドポイントを提供します。
-   **LangChain Agent (`app/agent.py`)**: システムの頭脳です。ユーザーの質問を解釈し、どのツールを使用すべきかを判断します。本プロジェクトでは、以下のツールを持っています。
    -   `local_document_search`: 社内ドキュメントを検索します。
    -   `search_github_repositories`: GitHubリポジトリを検索します。
    -   `browse_website`: 指定されたURLのウェブページの内容を取得します（Playwrightを利用）。
-   **CLI (`cli.py`)**: 管理者がドキュメントを取り込むためのコマンドラインインターフェースです。

### Tool Services
-   **Vector Store: ChromaDB**: 社内ドキュメントのベクトル検索用データベースです。
-   **LLM Service: Ollama**: 埋め込み生成とチャット応答生成を担当します。
-   **Playwright MCP Server**: `browse_website`ツールからのリクエストを受け、実際のブラウザ操作を実行するサーバーです。`docker-compose`によってNode.js環境で実行されます。
-   **GitHub MCP Server**: `search_github_repositories`ツールが呼び出す、GitHub公式の外部MCPサーバーです。

## 2.3. データフロー解説

基本的なチャットフローに加え、エージェントは質問内容に応じて異なるツールを呼び出します。

-   **社内文書に関する質問の場合**: `local_document_search`ツールが`Tool Server`と`ChromaDB`を呼び出します。
-   **GitHubに関する質問の場合**: `search_github_repositories`ツールが外部の`GitHub MCP Server`を呼び出します。
-   **特定のウェブサイトに関する質問の場合**: `browse_website`ツールが`Playwright MCP Server`コンテナを呼び出します。

エージェントは、これらのツールから得られた観測結果（Observation）を基に、最終的な回答を生成します。

## 2.4. 主要な設計判断

-   **マイクロサービス的なツール拡張**: `Playwright`のような異なる技術スタック（Node.js）で動作するツールも、Dockerコンテナとして追加し、サービス間通信を行うことで、Pythonベースのメインアプリケーションを汚染することなくシステム全体の機能を拡張できます。この疎結合なアプローチが、本システムの高い拡張性を支えています。
-   **依存性注入の活用**: `app/main.py`において、`agent_executor`をFastAPIの`Depends`を用いて注入しています。これにより、テスト容易性を大幅に向上させています。
-   **CLIによるIngestion**: ユーザーが直接APIを叩く負担を軽減するため、`markitdown`という強力なライブラリを活用したCLIツールを提供しました。
