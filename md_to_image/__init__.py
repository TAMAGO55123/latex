"""Markdownを画像(BytesIO)に変換するモジュール。"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_NODE_SCRIPT = _PROJECT_ROOT / "node" / "render.js"


class RenderError(Exception):
    """レンダリング処理中のエラー。"""


def _run_node(markdown: str) -> str:
    """Node.jsレンダラを呼び出し、HTMLを取得する。"""
    try:
        result = subprocess.run(
            ["node", str(_NODE_SCRIPT)],
            input=markdown.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RenderError(f"Node.js呼び出しエラー: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RenderError(f"HTML生成エラー (exit={result.returncode}): {stderr}")

    html = result.stdout.decode("utf-8")
    if not html.strip():
        raise RenderError("HTML生成エラー: 空の出力")
    return html


def _trim_image(img: Image.Image, padding: int = 16) -> Image.Image:
    """周囲の白い余白をトリミングする。"""
    if img.mode != "RGB":
        img = img.convert("RGB")
    gray = img.convert("L")
    mask = gray.point(lambda v: 0 if v >= 250 else 255)
    bbox = mask.getbbox()
    if bbox is None:
        return img
    left, upper, right, lower = bbox
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(img.width, right + padding)
    lower = min(img.height, lower + padding)
    return img.crop((left, upper, right, lower))


def render_markdown(
    markdown: str,
    width: int = 900,
    trim: bool = True,
) -> io.BytesIO:
    """Markdown文字列をPNG画像(BytesIO)にレンダリングする。"""
    if not isinstance(markdown, str):
        raise TypeError("markdown は文字列である必要があります")

    html = _run_node(markdown)

    tmp_dir = tempfile.mkdtemp()
    tmp_file = Path(tmp_dir) / "page.html"
    try:
        tmp_file.write_text(html, encoding="utf-8")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": width, "height": 800})
                    page.goto(tmp_file.as_uri(), wait_until="load")
                    page.wait_for_timeout(200)
                    png_bytes = page.screenshot(type="png", full_page=True)
                finally:
                    browser.close()
        except Exception as exc:
            raise RenderError(f"Playwrightエラー: {type(exc).__name__}: {exc}") from exc
    finally:
        try:
            tmp_file.unlink(missing_ok=True)
            os.rmdir(tmp_dir)
        except OSError:
            pass

    try:
        img = Image.open(io.BytesIO(png_bytes))
        if trim:
            img = _trim_image(img)
        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out
    except Exception as exc:
        raise RenderError(f"画像後処理エラー: {type(exc).__name__}: {exc}") from exc
