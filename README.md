# Markdown to Image

Markdownを高品質なPNG画像に変換するライブラリです。数式(KaTeX)とコードハイライト(Shiki)に対応しています。

## セットアップ (WSL2)

```bash
pipenv install
pipenv run playwright install chromium
npm install
```

## 使い方 (Python)

```python
from md_to_image import render_markdown
from io import BytesIO

buf: BytesIO = render_markdown("# Hello\n\n$E=mc^2$")
# buf は seek(0) 済みの PNG BytesIO
```

## Node.js レンダラ

```bash
node node/render.js < input.md > output.html
```

## テスト

```bash
pipenv run python -m pytest
```

## Discord Bot

```bash
export DISCORD_BOT_TOKEN="your_token_here"
pipenv run python bot.py
```

アプリコマンド `/render text:<Markdown>` で Markdown を画像化して返信します。

`$...$` を付け忘れた LaTeX 断片（`\text{}` や `\frac{}{}` など）は自動で `$...$` に包んで描画します。
