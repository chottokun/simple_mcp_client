# 2. アーキテクチャ (Architecture)

このドキュメントでは、インテリジェントRAGチャットシステムの技術的な構造と設計について詳細に解説します。

## 2.1. システム構成図

システムは、主に「Frontend」「Backend」「Tool Services」の3つのレイヤーで構成されています。設定とLLMクライアントの一元管理のため、`ConfigManager`と`LLMManager`を導入しています。

```mermaid
graph TD
    subgraph Browser
        A[Streamlit UI]
    end

    subgraph "Backend Server (Docker)"
        B[FastAPI: Chat API]
        C[LangChain: Agent/Orchestrator]
        LM[LLMManager]
        CM[ConfigManager]

        MCP_Client[MultiServerMCPClient]
        D[FastAPI: Tool Server]
    end

    subgraph "Tool Services (Docker / External)"
        G[Vector Store: ChromaDB]
        H[LLM Service: Ollama]
        PW[Playwright MCP Server]
        GH[GitHub MCP Server]
        E[env .env file]
    end

    E -- "Reads" --> CM
    CM -- "Provides config" --> LM
    CM -- "Provides config" --> D

    LM -- "Provides LLM" --> C
    LM -- "Provides Embeddings" --> D
    LM -- "Connects to" --> H

    A -- "1. /api/chat (HTTP)" --> B
    B -- "2. ainvoke(question)" --> C

    C -- "3. Decide which tool to use" --> D & MCP_Client

    subgraph "Internal Search Flow"
        D -- "Calls" --> G
    end

    subgraph "External MCP Tool Flow"
        C -- "Calls" --> MCP_Client
        MCP_Client -- "github" --> GH
        MCP_Client -- "playwright" --> PW
        GH -- "observation" --> MCP_Client
        PW -- "observation" --> MCP_Client
        MCP_Client -- "tool result" --> C
    end

    C -- "4. Generate final prompt" --> LM
    C -- "6. Return structured answer" --> B
    B -- "7. Return final response" --> A

    subgraph "Ingestion Flow (CLI)"
        I[CLI: cli.py]
        J[File (.pdf, .md, etc.)]
    end

    J -- "a. Read file" --> I
    I -- "b. /tools/ingest (HTTP)" --> D
```

## 2.2. コンポーネント詳細

### Frontend
-   **Streamlit UI (`streamlit_app.py`)**: ユーザーが直接操作するWebインターフェースです。

### Backend
-   **FastAPI: Chat API (`app/main.py`)**: ユーザーからのリクエストを受け付けるメインのAPIサーバーです。
-   **ConfigManager (`app/config.py`)**: `.env`ファイルから環境変数を読み込み、アプリケーション全体に設定を一元的に提供するシングルトンクラスです。
-   **LLMManager (`app/llm_manager.py`)**: LLMおよび埋め込みモデルのクライアントを生成・管理するシングルトンクラスです。`ConfigManager`から設定を読み取り、実際のOllamaクライアントまたはテスト用のモックを適切に提供します。
-   **LangChain Agent (`app/agent.py`)**: システムの頭脳です。`LLMManager`から提供されたLLMと、`MultiServerMCPClient`等から提供されたツールを用いて、ユーザーの質問に回答します。
-   **Tool Server & Tools (`app/tool_router.py`, `app/tools.py`)**: 社内文書の取り込み（ingest）と検索（search）のためのAPIとロジックです。文書の埋め込みには`LLMManager`から提供されたEmbedding Modelを利用します。
-   **MultiServerMCPClient (`app/agent.py`)**: `langchain-mcp-adapters`のクライアント。外部ツールサーバー（GitHub, Playwright）との接続を管理します。
-   **CLI (`cli.py`)**: 管理者がドキュメントを取り込むためのコマンドラインインターフェースです。

### Tool Services
-   **Vector Store: ChromaDB**: 社内ドキュメントのベクトル検索用データベースです。
-   **LLM Service: Ollama**: チャット応答生成と埋め込み生成を担当する、ローカルで実行されるLLMサービスです。
-   **Playwright MCP Server**: ブラウザ操作ツールを提供するサーバーです。
-   **GitHub MCP Server**: GitHub検索ツールを提供するサーバーです。

## 2.3. 主要な設計判断

-   **設定とクライアントの一元管理**: `ConfigManager`と`LLMManager`を導入し、シングルトンパターンで実装しました。これにより、設定の散在やLLMクライアントの多重生成を防ぎます。また、`MOCK_OLLAMA`フラグによるモックへの切り替えを、`LLMManager`内で確実に行えるようになり、テスト容易性が大幅に向上しました。
-   **MCPアダプタによる外部ツールの標準化**: `langchain-mcp-adapters`を導入し、外部APIとの通信を標準化・抽象化しました。これにより、コードの可読性と保守性が向上し、新しいMCPツールを簡単に追加できます。
-   **CLIによるIngestion**: ユーザーが直接APIを叩く負担を軽減するため、`markitdown`という強力なライブラリを活用したCLIツールを提供しました。
