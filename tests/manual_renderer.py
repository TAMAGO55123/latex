"""WSL上でMarkdownレンダリングを手動確認するCLIテスト。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md_to_image import RenderError, render_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MarkdownをPNGへ変換して、レンダリング結果を確認します。"
    )
    parser.add_argument(
        "markdown_file",
        nargs="?",
        type=Path,
        help="入力Markdownファイル。省略時は標準入力を使用します。",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("render-test.png"),
        help="出力PNGのパス（既定: render-test.png）",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=900,
        help="レンダリング幅（既定: 900）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        markdown = (
            args.markdown_file.read_text(encoding="utf-8")
            if args.markdown_file
            else sys.stdin.read()
        )
        image = render_markdown(markdown, width=args.width, trim=False)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(image.getvalue())
    except (OSError, RenderError) as exc:
        print(f"レンダリングテストに失敗しました: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"PNGを生成しました: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
