# インテリジェントRAGチャットシステム (Intelligent RAG Chat System)

## 概要 (Overview)

このプロジェクトは、社内に散在するドキュメント（規定、議事録、マニュアル等）を効率的に検索・活用するためのRAG (Retrieval-Augmented Generation) チャットシステムです。従業員は自然言語で質問するだけで、関連ドキュメントに基づいた正確な回答を迅速に得ることができます。

より詳細な情報については、`docs/`ディレクトリ内のドキュメントを参照してください。

-   **[はじめに (Introduction)](./docs/introduction.md)**: プロジェクトの目的、解決する課題、主な機能について。
-   **[アーキテクチャ (Architecture)](./docs/architecture.md)**: システムの技術的な構造と設計について。
-   **[開発者ガイド (Developer Guide)](./docs/development.md)**: 開発環境のセットアップ、テスト、コード品質について。
-   **[利用者ガイド (Usage Guide)](./docs/usage.md)**: チャットUIとドキュメント取り込み用CLIツールの使い方について。
-   **[ロードマップ (Roadmap)](./docs/roadmap.md)**: 今後のテスト戦略と機能拡張計画について。

## クイックスタート (Quick Start)

### 前提条件

-   [Docker](https://www.docker.com/get-started) と [Docker Compose](https://docs.docker.com/compose/install/)
-   ローカルで実行されている [Ollama](https://ollama.com/) と、必要なモデル (`nomic-embed-text`, `llama3`)
-   **GitHub Personal Access Token (PAT)**: `search_github_repositories`ツールを使用するために、`GITHUB_PAT`という名前の環境変数を設定する必要があります。

### 実行手順

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

4.  **ドキュメントの取り込み (Ingestion)**:
    `cli.py`ツールを使用してドキュメントを取り込みます。（詳細は[利用者ガイド](./docs/usage.md)を参照）
    ```bash
    # 依存関係のインストール (初回のみ)
    pip install -r requirements.txt

    # CLIツールの実行
    python cli.py ingest /path/to/your/document.pdf
    ```

5.  **コンテナを停止します。**
    ```bash
    sudo docker compose down
    ```
