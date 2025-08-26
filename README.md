# インテリジェントRAGチャットシステム (Intelligent RAG Chat System)

## 概要 (Overview)

このプロジェクトは、社内に散在するドキュメント（規定、議事録、マニュアル等）を効率的に検索・活用するためのRAG (Retrieval-Augmented Generation) チャットシステムです。従業員は自然言語で質問するだけで、関連ドキュメントに基づいた正確な回答を迅速に得ることができます。

より詳細な情報については、`docs/`ディレクトリ内のドキュメントを参照してください。

-   **[アーキテクチャ (Architecture)](./docs/architecture.md)**: システムの技術的な構造と設計について。
-   **[開発者ガイド (Developer Guide)](./docs/development.md)**: 開発環境のセットアップや詳細な設定について。

## クイックスタート (Quick Start)

### 1. 前提条件
-   [Docker](https://www.docker.com/get-started) と [Docker Compose](https://docs.docker.com/compose/install/)
-   ローカルで実行されている [Ollama](https://ollama.com/)

### 2. 環境設定
プロジェクトのルートに`.env`という名前のファイルを作成します。ほとんどの場合、空のままで動作しますが、必要に応じて設定を追加できます。

```dotenv
# GitHub検索ツールを利用する場合、ご自身のトークンをここに設定してください
# GITHUB_PAT=your_github_personal_access_token_here

# Docker for Mac/Windows以外でOllamaを利用する場合、URLを調整してください
# OLLAMA_BASE_URL=http://localhost:11434
```
*その他の設定可能な項目については、[開発者ガイド](./docs/development.md)を参照してください。*

### 3. システムの起動
```bash
# Dockerコンテナをビルドし、バックグラウンドで起動します
sudo docker compose up -d --build
```

### 4. アプリケーションへのアクセス
-   **チャットUI (Frontend)**: [http://localhost:8501](http://localhost:8501)
-   **APIドキュメント (Backend)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. ドキュメントの取り込み
`cli.py`ツールを使用して、検索対象のドキュメントをシステムに取り込みます。
```bash
# (初回のみ) 依存関係をインストール
pip install -r requirements.txt

# CLIツールを実行してドキュメントを取り込む
python cli.py ingest /path/to/your/document.pdf
```

### 6. システムの停止
```bash
sudo docker compose down
```
