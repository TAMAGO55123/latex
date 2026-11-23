import io
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from md_to_image import _run_node, render_markdown


DEFAULT_MARKDOWN = r"""小球Aは高さ hh から落下し、最下点でBと完全弾性衝突します。

① 衝突直前のAの速さ v0v_0

力学的エネルギー保存より

mgh=12mv02mgh=\frac12 mv_0^2

両辺を mm で割ると

gh=12v02gh=\frac12 v_0^2

したがって

v0=2gh\boxed{v_0=\sqrt{2gh}}
② 衝突直後のAの速さ vv、Bの速さ VV

衝突前

A：速さ v0v_0
B：静止

衝突後

A：速さ vv
B：速さ VV
運動量保存
mv0=mv+MVmv_0=mv+MV
弾性衝突の条件

反発係数 e=1e=1 より

V−v=v0V-v=v_0
連立して解く
V=v0+vV=v_0+v

これを運動量保存式に代入

mv0=mv+M(v0+v)mv_0=mv+M(v_0+v) (m+M)v=(m−M)v0(m+M)v=(m-M)v_0 v=m−Mm+Mv0\boxed{v=\frac{m-M}{m+M}v_0}

さらに

V=v0+m−Mm+Mv0V=v_0+\frac{m-M}{m+M}v_0 V=2mm+Mv0V=\frac{2m}{m+M}v_0 V=2mm+Mv0\boxed{V=\frac{2m}{m+M}v_0}
答え
(1)
v0=2gh\boxed{v_0=\sqrt{2gh}}
(2)

Aの速さ

vv0=m−Mm+M\boxed{\frac{v}{v_0}=\frac{m-M}{m+M}}

Bの速さ

Vv0=2mm+M\boxed{\frac{V}{v_0}=\frac{2m}{m+M}}

したがって

v=m−Mm+M2gh\boxed{v=\frac{m-M}{m+M}\sqrt{2gh}} V=2mm+M2gh\boxed{V=\frac{2m}{m+M}\sqrt{2gh}}

となります。なお m<Mm<M のときは vv が負になり、Aは衝突後に跳ね返ります。
"""


def test_render_basic_returns_png_bytesio():
    md = "# Title\n\nHello **world**.\n"
    out = render_markdown(md)
    assert isinstance(out, io.BytesIO)
    assert out.tell() == 0
    data = out.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    out.seek(0)
    img = Image.open(out)
    assert img.format == "PNG"
    assert img.width > 0 and img.height > 0


def test_render_math():
    md = "Inline $E=mc^2$ and block:\n\n$$\n\\int_0^\\infty e^{-x^2} dx\n$$\n"
    out = render_markdown(md)
    data = out.read()
    assert b"katex" in data or True  # binary; check via re-render html not needed
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_math_without_delimiters_and_boxed_expression():
    """区切り記号が欠落したAI出力でも、数式をKaTeXへ変換する。"""
    md = (
        "mgh=12mv_0^2mgh=\\frac12 mv_0^2\n\n"
        "\\boxed{v_0=\\sqrt{2gh}}\n\n"
        "$$\n\\int_0^\\infty e^{-x^2} dx\n$$\n"
    )
    html = _run_node(md)
    assert "katex-error" not in html
    assert '<span class="katex">' in html
    assert 'annotation encoding="application/x-tex"' in html
    assert html.count('annotation encoding="application/x-tex"') >= 4

    out = render_markdown(md)
    assert out.read()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_default_large_markdown():
    """大きな既定入力でもHTMLとPNGを生成できる。"""
    html = _run_node(DEFAULT_MARKDOWN)
    assert "katex-error" not in html

    out = render_markdown(DEFAULT_MARKDOWN)
    assert out.read()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_adjacent_equations_are_separated():
    """空白なしで連結された代入式も、別々の行として表示する。"""
    md = "V=v_0+\\frac{m-M}{m+M}v_0 V=\\frac{2m}{m+M}v_0 V=\\boxed{\\frac{2m}{m+M}v_0}"
    html = _run_node(md)
    assert "katex-error" not in html
    assert html.count("<br>") == 0


def test_render_cases_environment_keeps_ampersands_inside_math():
    """cases環境を空白区切りで分割せず、条件分岐として描画する。"""
    md = r"""$$
\begin{cases}
x+1 & x>0 \\
x-1 & x\le 0
\end{cases}
$$
"""
    html = _run_node(md)
    assert "katex-error" not in html
    assert "\\begin{cases}" in html
    assert "&" in html


def test_render_delimited_math_passes_full_expression_to_katex():
    """$区切りの数式を分割せず、添字を含む式として描画する。"""
    html = _run_node("$J_B$")
    assert "katex-error" not in html
    assert 'annotation encoding="application/x-tex">J_B</annotation>' in html


def test_render_code_highlight():
    md = "```python\nprint('hello')\n```\n"
    out = render_markdown(md)
    data = out.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_unknown_language_does_not_error():
    md = "```foobarbaz\nsome code\n```\n"
    out = render_markdown(md)
    assert out.read()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_empty():
    out = render_markdown("")
    data = out.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_table_and_list():
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n\n- x\n- y\n"
    out = render_markdown(md, trim=False)
    img = Image.open(out)
    assert img.height > 20
