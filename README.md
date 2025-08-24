# インテリジェントRAGチャットシステム (Intelligent RAG Chat System)

## 1. 概要 (Overview)

このプロジェクトは、社内に散在するドキュメント（規定、議事録、マニュアル等）を効率的に検索・活用するためのRAG (Retrieval-Augmented Generation) チャットシステムです。従業員は自然言語で質問するだけで、関連ドキュメントに基づいた正確な回答を迅速に得ることができます。

## 2. 技術スタック (Tech Stack)

| レイヤー                | 技術                 | 役割                                         |
| ----------------------- | -------------------- | -------------------------------------------- |
| **Frontend**            | Streamlit            | 迅速なUIプロトタイピングと実装               |
| **Backend**             | FastAPI              | 非同期処理に対応した高速なAPIサーバー        |
| **LLM Agent Framework** | LangChain            | LLM、ツール、プロンプトを統合し、Agentを構築 |
| **Tool Server**         | FastApiMCP           | FastAPIエンドポイントをLLM用ツールとして公開 |
| **Vector Store**        | ChromaDB             | ドキュメントのベクトル化と類似度検索         |
| **LLM**                 | Ollama (nomic-embed-text, llama3) | 埋め込み生成と自然言語応答生成             |
| **Container**           | Docker, Docker Compose | 開発・本番環境の再現性とポータビリティ     |
| **Code Quality**        | Ruff, Pytest         | リンティング、フォーマット、単体テスト       |

## 3. セットアップと実行 (Setup & Execution)

### 前提条件 (Prerequisites)

-   [Docker](https://www.docker.com/get-started) と [Docker Compose](https://docs.docker.com/compose/install/) がインストールされていること。
-   Ollamaがローカルで実行されており、必要なモデルがプルされていること。
    ```bash
    # For embeddings
    ollama pull nomic-embed-text

    # For chat generation
    ollama pull llama3
    ```

### 実行手順 (Running the Application)

1.  **リポジトリをクローンします。**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Dockerコンテナをビルドして起動します。**
    ```bash
    sudo docker compose build
    sudo docker compose up -d
    ```

3.  **アプリケーションへのアクセス:**
    -   **チャットUI (Frontend)**: [http://localhost:8501](http://localhost:8501)
    -   **APIドキュメント (Backend)**: [http://localhost:8000/docs](http://localhost:8000/docs)

4.  **コンテナを停止します。**
    ```bash
    sudo docker compose down
    ```

## 4. APIエンドポイント

### `/api/chat`

-   **Method**: `POST`
-   **役割**: ユーザーからのチャットメッセージを受け取り、LLMエージェントからの応答を返します。
-   **Request Body**:
    ```json
    {
      "message": "string",
      "session_id": "string"
    }
    ```
-   **Response Body**:
    ```json
    {
      "answer": "string",
      "sources": [
        {
          "document_name": "string",
          "snippet": "string"
        }
      ]
    }
    ```

### `/tools/ingest`

-   **Method**: `POST`
-   **役割**: ドキュメントをベクトルストアに取り込みます。
-   **Request Body**:
    ```json
    {
      "file_content": "string",
      "file_name": "string"
    }
    ```
