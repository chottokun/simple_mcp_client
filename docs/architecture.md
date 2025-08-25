# 2. アーキテクチャ (Architecture)

このドキュメントでは、インテリジェントRAGチャットシステムの技術的な構造と設計について詳細に解説します。

## 2.1. システム構成図

システムは、主に「Frontend」「Backend」「Tool Services」の3つのレイヤーで構成されています。`langchain-mcp-adapters`の導入により、外部ツールとの連携がより洗練されました。

```mermaid
graph TD
    subgraph Browser
        A[Streamlit UI]
    end

    subgraph "Backend Server (Docker)"
        B[FastAPI: Chat API]
        C[LangChain: Agent/Orchestrator]
        MCP_Client[MultiServerMCPClient]
        D[FastAPI: Tool Server]
        E[Tool: ingest_document]
        F[Tool: search_data]
    end

    subgraph "Tool Services (Docker / External)"
        G[Vector Store: ChromaDB]
        H[LLM Service: Ollama]
        PW[Playwright MCP Server]
        GH[GitHub MCP Server]
    end

    A -- "1. /api/chat (HTTP)" --> B
    B -- "2. ainvoke(question)" --> C

    C -- "3. Decide which tool to use" --> D & MCP_Client

    subgraph "Internal Search Flow"
        D -- "Calls" --> F
        F -- "query" --> G
        G -- "results" --> F
        F -- "JSON" --> D
        D -- "observation" --> C
    end

    subgraph "External MCP Tool Flow"
        C -- "Calls" --> MCP_Client
        MCP_Client -- "github" --> GH
        MCP_Client -- "playwright" --> PW
        GH -- "observation" --> MCP_Client
        PW -- "observation" --> MCP_Client
        MCP_Client -- "tool result" --> C
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
-   **FastAPI: Chat API (`app/main.py`)**: ユーザーからのリクエストを受け付けるメインのAPIサーバーです。アプリケーションの起動時に`lifespan`イベントハンドラを用いて、非同期に`AgentExecutor`を初期化します。
-   **FastAPI: Tool Server (`app/tool_router.py`)**: `local_document_search`ツールが使用する、`ingest`と`search`の内部APIエンドポイントを提供します。
-   **LangChain Agent (`app/agent.py`)**: システムの頭脳です。ユーザーの質問を解釈し、どのツールを使用すべきかを判断します。
-   **MultiServerMCPClient (`app/agent.py`)**: `langchain-mcp-adapters`ライブラリのクライアントです。`GitHub`や`Playwright`のような外部MCPサーバーへの接続を一元管理し、それらのサーバーが提供するツールを動的に読み込み、LangChainエージェントに提供します。
-   **CLI (`cli.py`)**: 管理者がドキュメントを取り込むためのコマンドラインインターフェースです。

### Tool Services
-   **Vector Store: ChromaDB**: 社内ドキュメントのベクトル検索用データベースです。
-   **LLM Service: Ollama**: 埋め込み生成とチャット応答生成を担当します。
-   **Playwright MCP Server**: `browse_website`ツールなどを提供するブラウザ操作用のサーバーです。`docker-compose`によってNode.js環境で実行されます。
-   **GitHub MCP Server**: `search_github_repositories`ツールなどを提供する、GitHub公式の外部MCPサーバーです。

## 2.3. データフロー解説

エージェントは、質問内容に応じて異なるツールを呼び出します。

-   **社内文書に関する質問の場合**: `local_document_search`ツールが`Tool Server`と`ChromaDB`を呼び出します。
-   **外部サービスに関する質問の場合**: エージェントは`MultiServerMCPClient`を通じて、適切な外部ツール（GitHubやPlaywright）を呼び出します。クライアントが各サーバーとの通信を抽象化するため、エージェントは統一されたインターフェースでツールを利用できます。

エージェントは、これらのツールから得られた観測結果（Observation）を基に、最終的な回答を生成します。

## 2.4. 主要な設計判断

-   **MCPアダプタによる標準化**: `langchain-mcp-adapters`を導入することで、これまで手動で行っていた外部API（MCPサーバー）との通信を標準化・抽象化しました。これにより、コードの可読性と保守性が向上し、新しいMCPツールを簡単に追加できるようになりました。
-   **非同期処理への移行**: エージェントの初期化やツールの非同期I/Oに対応するため、`app/main.py`ではFastAPIの`lifespan`イベントを、`app/agent.py`では`async/await`を全面的に採用しました。これにより、アプリケーションの起動や外部API呼び出しのパフォーマンスが向上します。
-   **CLIによるIngestion**: ユーザーが直接APIを叩く負担を軽減するため、`markitdown`という強力なライブラリを活用したCLIツールを提供しました。
