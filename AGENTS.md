\# AGENTS.md



\## Purpose



このプロジェクトは、AIが生成したMarkdownを高品質な画像としてレンダリングすることを目的とする。



対象用途:



\- Discord Bot

\- FastAPI

\- Flask

\- Quart

\- CLIツール

\- AI回答の画像化

\- 数式を含む回答の可視化

\- コードを含む回答の可視化



最終成果物は画像であり、APIは `BytesIO` を返却する。



\---



\## Communication Rules



開発・運用・AI支援における標準言語は日本語とする。



以下は日本語で記述すること。



\- README

\- 設計書

\- ドキュメント

\- コメント

\- Docstring

\- Issue

\- Pull Request

\- Commit Message

\- コードレビュー

\- エラーメッセージ

\- ログメッセージ

\- AIとのやり取り

\- AGENTS.md



ただし以下は英語表記を維持する。



\- クラス名

\- 関数名

\- モジュール名

\- ライブラリ名

\- API名

\- 標準規格

\- HTTP関連用語

\- OS・ミドルウェア等の正式名称



\---



\## Development Environment



標準開発環境は以下とする。



```text

Windows + WSL2

```



開発者はWSL2上で作業することを前提とする。



\### 想定環境



\#### 開発環境



```text

Windows 11

WSL2

Ubuntu LTS

```



\#### 実行環境



```text

Linux

Docker

Ubuntu LTS

Debian

```



\---



\## Platform Policy



本プロジェクトはLinux環境を優先する。



Windows専用APIへの依存は禁止とする。



利用禁止例:



\- WebView2

\- Win32 API

\- PowerShell依存

\- Windows Registry

\- COM

\- WMI



利用してよいもの:



\- Python

\- Node.js

\- Chromium

\- Playwright



\---



\## Path Handling



OS依存のパス結合は禁止。



必ず以下を利用すること。



```python

from pathlib import Path

```



推奨:



```python

path = Path("assets") / "font.ttf"

```



非推奨:



```python

path = "assets/font.ttf"

```



\---



\## Rendering Pipeline



レンダリング処理は以下の構成とする。



```text

Markdown

&#x20;   ↓

Node.js Renderer

&#x20;   ↓

HTML

&#x20;   ↓

Playwright + Chromium

&#x20;   ↓

PNG

&#x20;   ↓

Pillow（必要に応じて加工）

&#x20;   ↓

BytesIO

```



\---



\## Responsibilities



\### Python



Pythonは以下を担当する。



\- 公開API

\- Render管理

\- 一時ファイル管理

\- Node.js呼び出し

\- Playwright起動

\- Chromium制御

\- PNG取得

\- Pillow後処理

\- BytesIO生成



Markdown解析は行わない。



\---



\### Node.js



Node.jsは以下を担当する。



\- Markdown解析

\- LaTeX変換

\- コードハイライト

\- HTML生成



Node.jsはHTTPサーバーとして動作しない。



実行形式:



```text

Markdown

&#x20;   ↓

node process

&#x20;   ↓

HTML

```



\---



\## Dependency Policy



\### Python



パッケージ管理はPipenvを利用する。



必須ファイル:



```text

Pipfile

Pipfile.lock

```



導入禁止:



\- Poetry

\- uv

\- Conda



技術的理由がある場合のみ例外を認める。



\---



\### Node.js



Node.jsはレンダリング補助のみとする。



サーバーフレームワークは禁止。



利用禁止例:



\- React

\- Next.js

\- Vue

\- Nuxt

\- Angular

\- Webpack

\- Vite



ビルド工程を極力持たない。



\---



\## Preferred Libraries



\### Python



推奨:



```text

playwright

pillow

```



必要に応じて:



```text

pytest

```



\---



\### Node.js



推奨:



```text

markdown-it

katex

shiki

```



\---



\## Markdown Support



最低限対応すべき要素:



\- 見出し

\- 強調

\- 箇条書き

\- 番号付きリスト

\- 引用

\- コードブロック

\- インラインコード

\- テーブル

\- 水平線

\- 画像

\- リンク



AI出力の一般的なMarkdownはすべて正常表示できること。



\---



\## Math Rendering



数式描画にはKaTeXを使用する。



優先理由:



\- MathJaxより高速

\- 実行時レンダリング不要

\- HTML出力可能

\- 軽量



対応対象:



```markdown

$E = mc^2$



$$

\\int\_0^\\infty e^{-x^2} dx

$$

```



数式変換はNode.js側で完了させる。



ブラウザ側で数式処理を行わせない。



\---



\## Code Highlighting



コードハイライトにはShikiを使用する。



理由:



\- VSCode互換

\- 高品質

\- 言語認識が安定



デフォルトテーマ:



```text

github-light

```



未知の言語指定時:



```text

plaintext

```



として表示する。



エラーにしない。



\---



\## Font Policy



標準フォント:



```text

M PLUS 2

```



要件:



\- 日本語表示可能

\- CSSで読み込み可能

\- Linux環境で安定



フォールバック:



```css

"M PLUS 2",

"Noto Sans CJK JP",

sans-serif

```



\---



\## HTML Requirements



生成されるHTMLは以下を満たす。



\- 単独で表示可能

\- 外部依存なし

\- CDN利用禁止

\- 外部CSS禁止

\- 外部JavaScript禁止

\- オフライン動作可能



許可されるもの:



\- ローカルCSS

\- ローカルJavaScript

\- ローカルフォント



\---



\## Offline Policy



完全オフライン環境で動作可能であること。



禁止:



```html

https://cdn.jsdelivr.net/

https://unpkg.com/

https://cdnjs.cloudflare.com/

```



などへの依存。



ブラウザはネットワーク接続を必要としない。



\---



\## Browser Runtime



レンダラにはPlaywright Chromiumを利用する。



理由:



\- レンダリング品質

\- CSS互換性

\- スクリーンショット品質

\- 安定性



Chromium利用は許可される。



\---



\## Screenshot Policy



スクリーンショット取得はPlaywright標準機能を使用する。



例:



```python

page.screenshot(

&#x20;   type="png",

&#x20;   full\_page=True

)

```



\---



\## Image Post Processing



必要に応じてPillowによる以下の後処理を許可する。



\- 余白調整

\- トリミング

\- サイズ変更

\- 透過除去

\- Discord向け最適化



大幅な再描画は行わない。



\---



\## Output Contract



公開APIの返却型は以下とする。



```python

BytesIO

```



要件:



\- PNG形式

\- seek(0)済み

\- そのまま送信可能



対象:



```python

discord.File(...)

```



```python

StreamingResponse(...)

```



等。



\---



\## Memory Policy



可能な限りメモリ上で処理する。



推奨:



```python

BytesIO

```



非推奨:



```python

/tmp/output.png

```



最終成果物の保存を必須としない。



\---



\## Error Handling



例外を握り潰してはならない。



最低限出力する情報:



\- 処理フェーズ

\- 例外型

\- 元エラー内容



例:



```text

Markdown Parse Error

KaTeX Render Error

HTML Generation Error

Playwright Error

Screenshot Error

```



\---



\## Testing



テストはWSL2上で実行可能であること。



例:



```bash

pipenv run pytest

```



検証対象:



\- Markdown描画

\- 数式描画

\- コードハイライト

\- PNG出力

\- BytesIO出力



GUI環境に依存してはならない。



すべてHeadlessで動作すること。



\---



\## Performance Goals



目標性能:



|項目|目標|

|---|---|

|短い回答|1秒以内|

|長い回答|5秒以内|

|メモリ使用量|500MB未満|

|オフライン動作|必須|



\---



\## Security



Markdown入力は信頼しない。



禁止事項:



\- 任意JavaScript実行

\- 外部サイトアクセス

\- 任意コマンド実行

\- 任意ファイル読み込み



生成するHTMLは静的コンテンツとする。



\---



\## Future Extensions



将来的に追加してよい機能:



\- ダークテーマ

\- GitHub Darkテーマ

\- SVG出力

\- PDF出力

\- Mermaid対応

\- キャッシュ機能

\- Discordユーティリティ

\- FastAPI統合

\- 並列レンダリング



ただし基本構成を複雑化しないこと。



\---



\## Non-Goals



本プロジェクトは以下を目的としない。



\- Markdownエディタ

\- Webブラウザ

\- Webサービス

\- CMS

\- ノートアプリ

\- 共同編集システム



責務はただ一つである。



```text

Markdown → Image(BytesIO)

```

