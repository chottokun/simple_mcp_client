# 2. アーキテクチャ (Architecture)

このドキュメントでは、インテリジェントRAGチャットシステムの技術的な構造と設計について詳細に解説します。

## 2.1. システム構成図

システムは、主に「Frontend」「Backend」「Data & AI」の3つのレイヤーで構成されています。

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
    end

    subgraph "Data & AI Services (Docker / External)"
        G[Vector Store: ChromaDB]
        H[LLM Service: Ollama]
    end

    A -- "1. /api/chat (HTTP)" --> B
    B -- "2. invoke(question)" --> C
    C -- "3. Decide to use 'search' tool" --> D
    F -- "4. query(question)" --> G
    G -- "5. Return relevant chunks" --> F
    D -- "6. Return search results (JSON)" --> C
    C -- "7. Generate final prompt" --> H
    H -- "8. Return final answer (JSON)" --> C
    C -- "9. Return structured answer" --> B
    B -- "10. Return final response" --> A

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
-   **Streamlit UI (`streamlit_app.py`)**: ユーザーが直接操作するWebインターフェースです。迅速な開発とインタラクティブな要素の実装に適しているため、Streamlitが採用されました。チャット履歴の表示、ユーザー入力のハンドリング、そしてBackend APIとの通信を担当します。

### Backend
-   **FastAPI: Chat API (`app/main.py`)**: ユーザーからのリクエストを受け付けるメインのAPIサーバーです。非同期処理に強く、高いパフォーマンスが求められるためFastAPIが採用されました。`/api/chat`エンドポイントを提供し、LangChainエージェントの呼び出しをオーケストレーションします。
-   **FastAPI: Tool Server (`app/tool_router.py`, `fastapi-mcp`)**: LangChainエージェントが使用する「ツール」をAPIとして提供します。`/tools/ingest`や`/tools/search`といったエンドポイントを定義し、`fastapi-mcp`ライブラリによって、これらのエンドポイントがLLMエージェントから呼び出し可能な形式に変換されます。
-   **LangChain Agent (`app/agent.py`)**: システムの頭脳です。ユーザーの質問を解釈し、どのツールを使用すべきかを判断します。本プロジェクトでは、以下の2つのツールを持っています。
    -   `local_document_search`: 社内ドキュメントを検索します。
    -   `microsoft_docs_search`: Microsoft Learnの公式ドキュメントを検索します（現在は、実際のAPI応答を模した、高品質なプレースホルダー実装となっています）。
    エージェントはツールから得られた情報を基に、最終的な回答を生成するためのプロンプトを組み立て、LLMに送信します。思考と行動の連鎖を管理しやすい**ReAct (Reasoning and Acting)** タイプのエージェントを採用しています。
-   **CLI (`cli.py`)**: 管理者がドキュメントを取り込むためのコマンドラインインターフェースです。`markitdown`ライブラリを利用して様々なファイル形式をテキストに変換し、`/tools/ingest` APIを呼び出すことで、手動でのAPI操作を簡略化します。

### Data & AI Services
-   **Vector Store: ChromaDB**: ドキュメントのチャンク（分割されたテキスト）とそのベクトル表現を保存・検索するためのデータベースです。ローカル環境で容易に実行でき、LangChainとの親和性も高いことから採用されました。
-   **LLM Service: Ollama**: 埋め込みベクトル生成（`nomic-embed-text`）とチャット応答生成（`llama3`）の両方を担当するLLMサービスです。ローカル環境で実行できるため、開発サイクルを迅速に回すことができます。アーキテクチャは他のLLM（Azure OpenAIなど）にも容易に切り替えられるよう、疎結合に設計されています。

## 2.3. データフロー解説

### チャットフロー (Chat Flow)
1.  ユーザーがStreamlit UIで質問を入力し、送信します。
2.  UIはFastAPIの`/api/chat`エンドポイントにHTTP POSTリクエストを送信します。
3.  Chat APIはリクエストを受け取り、LangChainエージェントを呼び出します (`agent_executor.invoke`)。
4.  エージェントは質問を分析し、「`search`ツールを使うべきだ」と判断します。
5.  エージェントはTool Server (`/tools/search`) に質問内容を引数としてAPIコールを行います。
6.  Tool ServerはChromaDBにクエリを投げ、関連するドキュメントチャンクを取得します。
7.  取得したチャンクは、Tool ServerからエージェントにJSON形式で返されます。
8.  エージェントは、元の質問とツールから得られた情報を組み合わせ、最終回答を生成するためのプロンプトを組み立て、Ollamaに送信します。
9.  Ollamaはプロンプトに基づき、最終的な回答と引用元情報を含むJSON形式の文字列を生成し、エージェントに返します。
10. エージェントはこのJSON文字列をChat APIに返し、Chat APIはそれをパースしてHTTPレスポンスとしてStreamlit UIに返却します。
11. UIはレスポンスを整形し、ユーザーに回答と引用元を表示します。

### インジェストフロー (Ingestion Flow)
a.  管理者が`python cli.py ingest <ファイルパス>`コマンドを実行します。
b.  CLIツールは`markitdown`ライブラリを使い、指定されたファイル（PDFなど）の内容をプレーンテキストに変換します。
c.  変換されたテキストとファイル名をペイロードとして、FastAPIの`/tools/ingest`エンドポイントにHTTP POSTリクエストを送信します。
d.  Tool Serverは受け取ったテキストをチャンクに分割します。
e.  各チャンクについて、Ollama (`nomic-embed-text`) を呼び出して埋め込みベクトルを計算します。
f.  テキストチャンク、埋め込みベクトル、そしてメタデータ（ファイル名）をChromaDBに保存します。

## 2.4. 主要な設計判断

-   **FastAPIの採用**: 高速なパフォーマンスと、Pydanticによる厳密な型検証、そして自動生成されるAPIドキュメントが、堅牢なバックエンド開発に適していると判断しました。
-   **依存性注入の活用**: `app/main.py`において、`agent_executor`をFastAPIの`Depends`を用いて注入しています。これにより、アプリケーションの起動時にLLMへの接続が発生するのを防ぎ、テスト容易性を大幅に向上させています。
-   **疎結合なツール設計**: LangChainエージェントは、ツールの具体的な実装を知りません。HTTP経由でTool Serverを呼び出すだけです。これにより、将来的にツールを別のマイクロサービスとして切り出すといった拡張が容易になります。
-   **CLIによるIngestion**: ユーザーが直接APIを叩く負担を軽減するため、`markitdown`という強力なライブラリを活用したCLIツールを提供しました。これにより、様々なファイル形式の取り込みが統一されたインターフェースで可能になります。
