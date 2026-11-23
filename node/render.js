const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const MarkdownIt = require('markdown-it');
const katex = require('katex');

let shikiCore = null;
function loadShikiCore() {
  if (shikiCore) return shikiCore;
  try {
    const core = require('shiki/core');
    const themes = require('shiki/themes');
    const langs = require('shiki/langs');
    shikiCore = {
      createHighlighterCore: core.createHighlighterCore,
      createJavaScriptRegexEngine: core.createJavaScriptRegexEngine,
      bundledThemes: themes.bundledThemes,
      bundledLanguages: langs.bundledLanguages,
    };
  } catch (e) {
    shikiCore = null;
  }
  return shikiCore;
}

function normalizeLang(lang) {
  const l = (lang || '').toLowerCase();
  const aliases = {
    js: 'javascript', jsx: 'javascript', ts: 'typescript', tsx: 'typescript',
    py: 'python', rb: 'ruby', sh: 'bash', shell: 'bash', zsh: 'bash',
    yml: 'yaml', md: 'markdown', html: 'html', htm: 'html',
  };
  return aliases[l] || l;
}

const ROOT = path.resolve(__dirname, '..');
const FONT_PATH = path.join(ROOT, 'assets', 'fonts', 'MPLUS2[wght].ttf');
const KATEX_CSS_PATH = path.join(ROOT, 'node_modules', 'katex', 'dist', 'katex.min.css');
const KATEX_FONT_DIR = path.join(ROOT, 'node_modules', 'katex', 'dist', 'fonts');

function embedKatexCss() {
  let css = fs.readFileSync(KATEX_CSS_PATH, 'utf8');
  css = css.replace(/url\(fonts\/([^)]+)\)/g, (match, file) => {
    const abs = path.join(KATEX_FONT_DIR, file);
    return `url(${pathToFileURL(abs).href})`;
  });
  return css;
}

function legacyAutoWrapMath(src) {
  // 既存の数式 ($...$ / $$...$$) を保護
  const mathStore = [];
  let s = src.replace(/\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$/g, (m) => {
    mathStore.push(m);
    return `\u0000MATH${mathStore.length - 1}\u0000`;
  });
  // インラインコードを保護
  const codeStore = [];
  s = s.replace(/`[^`\n]+`/g, (m) => {
    codeStore.push(m);
    return `\u0000CODE${codeStore.length - 1}\u0000`;
  });

  // バックスラッシュコマンドを含む連続した「数式らしい」文字列を $...$ で包む
  s = s.replace(/(?:\\[a-zA-Z]+(?:\{[^}]*\})*|[\d\s+\-*/=^_().,a-zA-Z/<>\u00d7\u2212\u2264\u2265])+/g, (run) => {
    if (!/[\\_^=<>]/.test(run)) return run;
    const trimmed = run.trim();
    if (!trimmed) return run;
    // 前後の空白を保持しつつ包む
    const leading = run.match(/^\s*/)[0];
    const trailing = run.match(/\s*$/)[0];
    return leading + '$' + trimmed + '$' + trailing;
  });

  // 保護を復元
  s = s.replace(/\u0000CODE(\d+)\u0000/g, (_, idx) => codeStore[Number(idx)]);
  s = s.replace(/\u0000MATH(\d+)\u0000/g, (_, idx) => mathStore[Number(idx)]);
  return s;
}

function legacyProcessMath(src) {
  const parts = src.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (i % 2 === 1) return part;
    const inlineCodes = [];
    let s = part.replace(/`[^`\n]+`/g, (m) => {
      inlineCodes.push(m);
      return `\u0000IC${inlineCodes.length - 1}\u0000`;
    });

    // $ を付け忘れた LaTeX 断片を自動で $...$ に包む
    s = autoWrapMath(s);

    s = s.replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => {
      try {
        return katex.renderToString(math.trim(), { displayMode: true, throwOnError: false });
      } catch (e) {
        return `<pre>${math}</pre>`;
      }
    });
    s = s.replace(/\$([^\$\n]+?)\$/g, (_, math) => {
      try {
        return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false });
      } catch (e) {
        return `$${math}$`;
      }
    });
    s = s.replace(/\u0000IC(\d+)\u0000/g, (_, idx) => inlineCodes[Number(idx)]);
    return s;
  }).join('');
}

function renderKatex(math, displayMode = false) {
  try {
    return katex.renderToString(math.trim(), { displayMode, throwOnError: false });
  } catch (e) {
    return escapeHtml(math);
  }
}

function splitMathExpressions(math) {
  const expressions = [];
  let start = 0;
  let depth = 0;
  for (let i = 0; i < math.length; i += 1) {
    const char = math[i];
    if (char === '{') depth += 1;
    else if (char === '}') depth = Math.max(0, depth - 1);
    if (depth !== 0 || i <= start) continue;

    const startsAssignment = /^[A-Za-z][A-Za-z0-9_]*\s*=/.test(math.slice(i));
    const startsBoxed = math.startsWith('\\boxed', i);
    const isSpace = /\s/.test(char);
    if (!startsAssignment && !startsBoxed && !isSpace) continue;

    const expression = math.slice(start, i).trim();
    if (expression) expressions.push(expression);
    while (isSpace && i + 1 < math.length && /\s/.test(math[i + 1])) i += 1;
    start = i + 1;
  }
  const last = math.slice(start).trim();
  if (last) expressions.push(last);
  return expressions;
}

function renderSpacedMath(math, displayMode = false) {
  // cases/aligned などの環境は、& や改行が環境の構文の一部になる。
  // 空白区切りの数式分割を行うと環境ごと分断されてKaTeXエラーになるため、
  // 環境を含む数式は1つの式として描画する。
  if (/\\begin\s*\{[^}]+\}/.test(math)) {
    return renderKatex(math, displayMode);
  }
  const tokens = splitMathExpressions(math);
  const rendered = tokens.map((token) => renderKatex(token, false)).join(' ');
  const sequence = `<span class="math-sequence">${rendered}</span>`;
  return displayMode ? `<div class="katex-display">${sequence}</div>` : sequence;
}

function replaceDelimitedMath(src) {
  return src
    .replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => renderSpacedMath(math, true))
    .replace(/\$([^$\n]+?)\$/g, (_, math) => renderSpacedMath(math));
}

function isMathOnlyLine(line) {
  const text = line.trim();
  if (!text || /[\u3040-\u30ff\u3400-\u9fff]/.test(text)) return false;
  if (/^(#{1,6}|[-*+]\s|\d+[.)]\s|>\s)/.test(text)) return false;
  return /\\[a-zA-Z]+|[_^]|[=<>]|[×÷≤≥−]/.test(text);
}

function autoWrapMath(src) {
  // $ 区切りが欠落した AI 出力では、独立した数式行だけを補完する。
  return src.split('\n').map((line) => {
    if (!isMathOnlyLine(line)) return line;
    const leading = line.match(/^\s*/)[0];
    const trailing = line.match(/\s*$/)[0];
    return `${leading}$${line.trim()}$${trailing}`;
  }).join('\n');
}

function processMath(src) {
  const parts = src.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (i % 2 === 1) return part;
    const protectedParts = [];
    let s = part.replace(/`[^`\n]+`/g, (m) => {
      protectedParts.push(m);
      return `\u0000PROTECTED${protectedParts.length - 1}\u0000`;
    });
    const renderedMath = [];
    s = s.replace(/\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g, (whole, display, inline) => {
      // 明示された区切り内の内容は分割せず、そのままKaTeXへ渡す。
      // 添字（J_B）や cases の & など、数式全体の構文を保持する必要がある。
      renderedMath.push(renderKatex(display ?? inline, Boolean(display)));
      return `\u0000MATH${renderedMath.length - 1}\u0000`;
    });
    s = autoWrapMath(s);
    s = replaceDelimitedMath(s);

    // $ がない \boxed{...} なども、入れ子の括弧を追跡して処理する。
    s = s.replace(/\u0000PROTECTED(\d+)\u0000/g, (_, idx) => protectedParts[Number(idx)]);
    return s.replace(/\u0000MATH(\d+)\u0000/g, (_, idx) => renderedMath[Number(idx)]);
  }).join('');
}

async function main() {
  const input = fs.readFileSync(0, 'utf8');

  const hasCode = /```/.test(input);

  // collect languages used in fenced code blocks
  const usedLangs = new Set();
  if (hasCode) {
    for (const m of input.matchAll(/```([A-Za-z0-9_+-]*)/g)) {
      usedLangs.add(normalizeLang(m[1]));
    }
  }

  let highlighter = null;
  const sc = hasCode ? loadShikiCore() : null;
  if (sc) {
    try {
      highlighter = await sc.createHighlighterCore({
        themes: [sc.bundledThemes['github-light']],
        langs: [],
        engine: sc.createJavaScriptRegexEngine(),
      });
      for (const l of usedLangs) {
        const loader = sc.bundledLanguages[l];
        if (loader) {
          try { await highlighter.loadLanguage(loader); } catch (e) { /* ignore */ }
        }
      }
    } catch (e) {
      highlighter = null;
    }
  }

  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: false,
    breaks: false,
  });

  md.renderer.rules.fence = (tokens, idx) => {
    const token = tokens[idx];
    const info = (token.info || '').trim();
    const rawLang = info.split(/\s+/)[0] || '';
    const lang = normalizeLang(rawLang);
    const code = token.content;
    if (!highlighter) {
      return `<pre><code>${escapeHtml(code)}</code></pre>`;
    }
    const loaded = (typeof highlighter.getLoadedLanguages === 'function')
      ? highlighter.getLoadedLanguages() : [];
    const useLang = (lang && loaded.indexOf(lang) !== -1) ? lang : null;
    if (!useLang) {
      return `<pre class="shiki github-light" style="background-color:#f6f8fa" tabindex="0"><code>${escapeHtml(code)}</code></pre>`;
    }
    try {
      return highlighter.codeToHtml(code, { lang: useLang, theme: 'github-light' });
    } catch (e) {
      return `<pre><code>${escapeHtml(code)}</code></pre>`;
    }
  };

  const processed = processMath(input);
  const bodyHtml = md.render(processed);

  const fontUrl = pathToFileURL(FONT_PATH).href;
  const katexCss = embedKatexCss();

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
@font-face {
  font-family: "M PLUS 2";
  src: url(${fontUrl}) format('truetype');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
${katexCss}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #ffffff;
  color: #24292f;
  font-family: "M PLUS 2", "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
  font-size: 16px;
  line-height: 1.7;
}
.container {
  max-width: 820px;
  margin: 0 auto;
  padding: 32px 40px;
}
h1, h2, h3, h4, h5, h6 {
  margin-top: 1.4em;
  margin-bottom: 0.6em;
  font-weight: 700;
  line-height: 1.3;
}
h1 { font-size: 2em; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
h3 { font-size: 1.25em; }
p { margin: 0.8em 0; }
a { color: #0969da; text-decoration: none; }
ul, ol { padding-left: 2em; margin: 0.8em 0; }
li { margin: 0.3em 0; }
blockquote {
  margin: 1em 0;
  padding: 0.5em 1em;
  border-left: 4px solid #d0d7de;
  color: #57606a;
  background: #f6f8fa;
}
code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.9em;
  background: #f6f8fa;
  padding: 0.2em 0.4em;
  border-radius: 6px;
}
pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  line-height: 1.5;
}
pre code { background: transparent; padding: 0; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}
th, td {
  border: 1px solid #d0d7de;
  padding: 8px 12px;
}
th { background: #f6f8fa; font-weight: 600; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 1.5em 0; }
img { max-width: 100%; }
.katex { font-size: 1.1em; }
.katex-display { margin: 1em 0; overflow-x: auto; }
.math-sequence { display: inline-block; white-space: nowrap; }
.shiki { padding: 16px; border-radius: 8px; overflow-x: auto; }
</style>
</head>
<body>
<div class="container">
${bodyHtml}
</div>
</body>
</html>`;

  process.stdout.write(html);
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

main().catch((err) => {
  process.stderr.write(String(err && err.stack ? err.stack : err) + '\n');
  process.exit(1);
});
