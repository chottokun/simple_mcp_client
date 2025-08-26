# 3. 開発者ガイド (Developer Guide)

このドキュメントは、本プロジェクトの開発に参加する開発者向けのガイドです。

## 3.1. 主要な設計とコンセプト

### 設定とLLMクライアントの一元管理

本プロジェクトでは、設定とLLMクライアントの管理を、以下の2つのシングルトンクラスに集約しています。

-   **`app.config.ConfigManager`**:
    -   `.env`ファイルから環境変数を読み込み、アプリケーション全体に設定を一元的に提供します。
    -   Ollamaのモデル名や外部サービスのAPIキーなど、すべての環境依存の設定はこのクラスを通じて取得します。

-   **`app.llm_manager.LLMManager`**:
    -   LLMおよび埋め込みモデルのクライアントを生成・管理します。
    -   `ConfigManager`から設定を読み取り、実際のOllamaクライアントまたはテスト用のモックを適切に提供します。
    -   アプリケーション内のどの部分からでも、`llm_manager.get_llm()`や`llm_manager.get_embedding_model()`を呼び出すことで、同一のクライアントインスタンスを取得できます。

この設計により、設定の散在やクライアントの多重生成を防ぎ、テスト容易性を大幅に向上させています。

## 3.2. 開発環境のセットアップ

開発はDockerコンテナ内で行うことを強く推奨します。

### 1. 前提条件
-   [Docker](https://www.docker.com/get-started) と [Docker Compose](https://docs.docker.com/compose/install/)
-   ローカルで実行されている [Ollama](https://ollama.com/)
-   リポジトリのクローン

### 2. 環境変数の設定 (`.env`ファイル)
プロジェクトのルートに`.env`ファイルを作成し、必要な環境変数を設定します。

```dotenv
# GitHubリポジトリ検索ツールを使用するための個人アクセストークン
GITHUB_PAT=your_github_personal_access_token_here

# --- Ollamaの設定 (お使いの環境に合わせて変更) ---
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_CHAT_MODEL=llama3
OLLAMA_EMBED_MODEL=nomic-embed-text

# --- テスト用の設定 ---
# Ollamaへの実際の接続を行わず、モックを使用する場合はtrueに設定
# MOCK_OLLAMA=true
```
-   `GITHUB_PAT`: GitHub検索ツールを利用する場合に必須です。
-   `OLLAMA_BASE_URL`: OllamaサーバーのURL。Docker for Mac/Windowsでは`host.docker.internal`がホストマシンを指します。
-   `OLLAMA_CHAT_MODEL`: チャット応答用のモデル。
-   `OLLAMA_EMBED_MODEL`: 埋め込みベクトル生成用のモデル。
-   `MOCK_OLLAMA`: `true`に設定すると、Ollamaに接続せず、`LLMManager`が提供するモックオブジェクトを使用します。これにより、オフライン環境での開発やテストが可能になります。

### 3. コンテナのビルドと起動
```bash
# イメージをビルドし、コンテナをバックグラウンドで起動します
sudo docker compose up -d --build
```
-   フロントエンド: `http://localhost:8501`
-   バックエンドAPI: `http://localhost:8000`

## 3.3. テストとコード品質

-   **テストの実行**:
    ```bash
    # コンテナ内でテストを実行する場合
    sudo docker compose exec backend pytest

    # ローカルで実行する場合
    PYTHONPATH=. pytest
    ```

-   **コード品質**:
    コミット前には`ruff`によるフォーマットとチェックを実行してください。
    ```bash
    # フォーマット
    ruff format .

    # リンティングと自動修正
    ruff check . --fix
    ```

## 3.4. プロジェクト構造

```
.
├── app/
│   ├── __init__.py
│   ├── agent.py          # LangChainエージェントの定義
│   ├── config.py         # ★ ConfigManager
│   ├── llm_manager.py    # ★ LLMManager
│   ├── main.py           # FastAPIアプリケーションのメインファイル
│   ├── tool_router.py    # ツールのAPIエンドポイント定義
│   └── tools.py          # ツールのコアロジック
...
```
