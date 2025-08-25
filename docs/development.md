# 3. 開発者ガイド (Developer Guide)

このドキュメントは、本プロジェクトの開発に参加する開発者向けのガイドです。

## 3.1. 開発環境のセットアップ

開発はDockerコンテナ内で行うことを強く推奨します。

1.  **前提条件**:
    -   [Docker](https://www.docker.com/get-started) と [Docker Compose](https://docs.docker.com/compose/install/)
    -   ローカルで実行されている [Ollama](https://ollama.com/)
    -   リポジトリのクローン

2.  **環境変数の設定**:
    `search_github_repositories`ツールを使用するには、GitHubの個人アクセストークン（PAT）が必要です。プロジェクトのルートに`.env`ファイルを作成し、以下のように記述してください。Docker Composeが自動で読み込みます。
    ```
    GITHUB_PAT=your_github_personal_access_token_here
    ```
    *注意: `.env`ファイルは`.gitignore`に含まれており、バージョン管理されません。*

3.  **Ollamaモデルの準備**:
    開発には埋め込みモデルとチャットモデルが必要です。
    ```bash
    ollama pull nomic-embed-text
    ollama pull llama3
    ```

3.  **Dockerコンテナのビルド**:
    プロジェクトルートで以下のコマンドを実行し、`backend`と`frontend`のイメージをビルドします。
    ```bash
    sudo docker compose build
    ```

4.  **コンテナの起動**:
    すべてのサービス（`backend`, `frontend`, `chroma`, `playwright`）をバックグラウンドで起動します。
    ```bash
    sudo docker compose up -d
    ```
    -   フロントエンド: `http://localhost:8501`
    -   バックエンドAPI: `http://localhost:8000`

5.  **リアルタイムログの確認**:
    各サービスのログを確認するには、以下のコマンドを使用します。
    ```bash
    # バックエンドのログ
    sudo docker compose logs -f backend

    # フロントエンドのログ
    sudo docker compose logs -f frontend
    ```

## 3.2. テスト (Testing)

本プロジェクトでは`pytest`を使用した単体テストが導入されています。

-   **テストの実行**:
    すべてのテストを実行するには、プロジェクトルートで以下のコマンドを実行します。`PYTHONPATH`を設定することで、`app`モジュールを正しくインポートできます。
    ```bash
    PYTHONPATH=. pytest
    ```

-   **テストの場所**:
    テストコードはすべて`tests/`ディレクトリに配置されています。
    -   `tests/test_tools.py`: データ層のツール（`ingest_document`, `search_data`）のロジックをテストします。
    -   `tests/test_main.py`: FastAPIのエンドポイント（`/api/chat`）の動作をテストします。

## 3.3. コード品質 (Code Quality)

コードの品質と一貫性を保つために`Ruff`を使用しています。

-   **フォーマット**:
    コードを整形するには、以下のコマンドを実行します。
    ```bash
    ruff format .
    ```

-   **リンティングと自動修正**:
    静的解析と簡単な問題の自動修正を行うには、以下のコマンドを実行します。
    ```bash
    ruff check . --fix
    ```

コミット前には、必ず`ruff format`と`pytest`を実行してください。

## 3.4. 主要ライブラリ (Key Libraries)

本プロジェクトは、以下の主要なライブラリに依存しています。

-   **FastAPI**: 高パフォーマンスなWeb APIフレームワーク。
-   **LangChain**: LLMアプリケーションを構築するためのフレームワーク。エージェントやツール管理の根幹を担います。
-   **langchain-mcp-adapters**: 外部のMCP(Model Context Protocol)ツールサーバーとの接続を容易にするためのアダプタライブラリ。
-   **Streamlit**: フロントエンドのUIを構築するためのPythonライブラリ。
-   **ChromaDB**: ドキュメントのベクトル検索に使用するVector Store。
-   **Ollama**: ローカル環境でLLMを実行するためのツール。

## 3.5. プロジェクト構造

```
.
├── app/                  # FastAPIバックエンドのソースコード
│   ├── __init__.py
│   ├── agent.py          # LangChainエージェントの定義
│   ├── main.py           # FastAPIアプリケーションのメインファイル
│   ├── tool_router.py    # ツールのAPIエンドポイント定義
│   └── tools.py          # ツールのコアロジック（ChromaDBとの連携など）
│
├── data/                 # （ローカルテスト用）サンプルドキュメント
│   └── test_document.txt
│
├── docs/                 # プロジェクトドキュメント
│   ├── introduction.md   # プロジェクト概要
│   ├── architecture.md   # アーキテクチャ設計
│   ├── development.md    # 開発者ガイド
│   ├── usage.md          # ユーザーガイド
│   └── roadmap.md        # 将来計画
│
├── tests/                # テストコード
│   ├── test_main.py
│   └── test_tools.py
│
├── .gitignore
├── Agents.md             # (開発エージェント向け指示書)
├── cli.py                # ドキュメント取り込み用CLIツール
├── Dockerfile            # バックエンド用Dockerfile
├── Dockerfile.streamlit  # フロントエンド用Dockerfile
├── README.md             # プロジェクトの入り口
├── requirements.txt      # バックエンドとCLIの依存関係
├── requirements.streamlit.txt # フロントエンドの依存関係
├── status.md             # (開発エージェント向け進捗管理ファイル)
└── docker-compose.yml    # Docker Compose設定ファイル
```
