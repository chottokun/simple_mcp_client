# Agents.md

## Rules
- test-driven development; TDDを利用する。LLMなどの大規模モデルは必ずモックを利用し、Virtual Machineの容量を圧迫させないこと。
- 作業項目が多い場合は、段階に区切り、git commit を行いながら進めること
  - semantic commit を使用する
- コマンドの出力が確認できない場合、 get last command / check background terminal を使用して確認すること

## Develop
- 都度 status.md に開発状況と現在のタスクを記載しチェックを怠らないこと
- /docs を読み込み、要件に関連性のある記載を必ず分析・確認すること。

## Dev environment tips
- Use `uv` to create and manage your envireroment.
- Run `pip install -r requirements.txt` to install dependencies.
- Check code style using `ruff`

## Testing instructions
- Run the test suite with `pytest tests/`.

## PR instructions
- Title format: [<module_name>] <short description>
- Always run `ruff` and `pytest` before committing.
- Add reviewers as per CODEOWNERS.
