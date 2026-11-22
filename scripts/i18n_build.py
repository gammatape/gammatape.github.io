"""Build site/i18n_en.js for the VI / EN switch (site/i18n.js), 2026-11-20.

Two kinds of entries, both Vietnamese -> English:

* Units (window.WD_I18N_UNITS): a whole block of static HTML - a paragraph, list item, heading, button... - whose
  children are only inline elements (b, a, span, br...). The key is the block's text with every inline element
  written as a marker: "Bấm {0}Cài đặt{/0}, rồi mở {1}Tailscale{/1}." (void elements such as <br>, <img>, <svg>:
  "{2/}"). The English value uses the same markers, in whatever order English needs, so a sentence with bold words
  or links in the middle is translated as one sentence. site/i18n.js builds the same key from the DOM.
* Fragments (window.WD_I18N_EN): every other Vietnamese string that can reach the screen - attributes (title,
  placeholder, aria-label, alt, meta content), text outside units, string literals in the pages' scripts and
  site/*.js (template literals split at ${...}), and the labels scripts/fetch_market.py writes into the data
  (its scenario sentences are already written in both languages), plus the news source names in feeds.json.
  Code that calls I18N.t("vi", "en") carries its own English and needs no entry.

Translations live in scripts/i18n_en.json (fragments) and scripts/i18n_units_en.json (units). Only entries still in
use are written out. Missing ones are printed; --strict exits 1 when any is missing (run it before committing).

    py -B scripts/i18n_build.py            # build + list missing
    py -B scripts/i18n_build.py --dump     # also write scripts/i18n_missing*.json (what still needs translating)
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
FRAG_DICT = ROOT / "scripts" / "i18n_en.json"
UNIT_DICT = ROOT / "scripts" / "i18n_units_en.json"
VI = re.compile("[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
                "ĂÂĐÊÔƠƯÀÁẢÃẠẰẮẲẴẶẦẤẨẪẬÈÉẺẼẸỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌỒỐỔỖỘỜỚỞỠỢÙÚỦŨỤỪỨỬỮỰỲÝỶỸỴ]")
ATTRS = {"title", "placeholder", "aria-label", "alt"}
# must match INLINE / ATOMIC in site/i18n.js
INLINE = {"a", "b", "strong", "i", "em", "span", "small", "code", "kbd", "sup", "sub", "mark", "u", "s", "time", "abbr"}
ATOMIC = {"br", "img", "svg", "wbr"}
SKIP = {"script", "style", "textarea", "pre", "template", "noscript"}
JS_STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`', re.S)
TPL_EXPR = re.compile(r"\$\{((?:[^{}]|\{[^{}]*\})*)\}")
PAIR = re.compile(r'I18N\.t\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def js_fragments(code, out):
    code = re.sub(r"(?m)^\s*//.*$", "", code)
    for m in JS_STR.finditer(code):
        s = next(g for g in m.groups() if g is not None)
        if m.group(3) is not None:  # template literal: strings inside ${...}, then the text between them
            for e in TPL_EXPR.finditer(s):
                js_fragments(e.group(1), out)
            parts = TPL_EXPR.split(s)[::2]
        else:
            parts = [s]
        for p in parts:
            p = p.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
            for piece in re.split(r"<[^>]+>", p):  # strings that carry markup: only the text between tags
                piece = norm(piece)
                if VI.search(piece):
                    out.add(piece)


# ------------------------------------------------------------------ units (same algorithm as site/i18n.js)
def skipped(el):
    return el.name in SKIP or el.has_attr("data-i18n-skip") or el.get("translate") == "no"


def only_inline(el):
    for d in el.descendants:
        if isinstance(d, Tag):
            if skipped(d) or (d.name not in INLINE and d.name not in ATOMIC):
                return False
            if d.name in ATOMIC:
                continue
    return True


def template(el):
    n = [0]

    def rec(node):
        s = ""
        for c in node.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                s += str(c)
            elif isinstance(c, Tag):
                i = n[0]
                n[0] += 1
                s += f"{{{i}/}}" if c.name in ATOMIC else f"{{{i}}}{rec(c)}{{/{i}}}"
        return s

    return norm(rec(el))


def walk_page(soup, units, frags):
    def visit(el):
        if skipped(el):
            if el.name == "script" and not el.get("src") and el.string:
                js_fragments(el.string, frags)
            return
        for k, v in el.attrs.items():
            if isinstance(v, str) and VI.search(v) and (k in ATTRS or (el.name == "meta" and k == "content")):
                frags.add(norm(v))
        if el.name not in ("html", "head", "body") and el.name not in ATOMIC and only_inline(el) \
                and VI.search(el.get_text()):
            units.add(template(el))
            for d in el.descendants:  # attributes inside a unit still need fragments
                if isinstance(d, Tag):
                    for k, v in d.attrs.items():
                        if isinstance(v, str) and VI.search(v) and k in ATTRS:
                            frags.add(norm(v))
            return
        for c in el.children:
            if isinstance(c, Tag):
                visit(c)
            elif isinstance(c, NavigableString) and not isinstance(c, Comment) and VI.search(c):
                frags.add(norm(c))   # loose text beside block children: fragment

    visit(soup)


def py_fragments(path, out):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "scenarios":   # written in both languages
            skip.update(id(n) for n in ast.walk(node))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):  # docstrings
            skip.add(id(node.value))
    for node in ast.walk(tree):
        if id(node) in skip or not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        s = node.value
        if VI.search(s) and not s.startswith(("  !", "#")) and "\n" not in s and len(s) < 300:
            out.add(norm(s))


def collect():
    units, frags = set(), set()
    for p in sorted(SITE.rglob("*.html")):
        walk_page(BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser"), units, frags)
    for p in sorted(SITE.glob("*.js")):
        if not p.name.startswith("i18n"):
            js_fragments(p.read_text(encoding="utf-8"), frags)
    py_fragments(ROOT / "scripts" / "fetch_market.py", frags)
    for f in json.loads((ROOT / "feeds.json").read_text(encoding="utf-8")).get("feeds", []):
        if isinstance(f, dict) and VI.search(f.get("name", "")):
            frags.add(norm(f["name"]))
    return units, frags


def markers(s):
    return sorted(re.findall(r"\{/?\d+/?\}", s))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    units, frags = collect()
    have = json.loads(FRAG_DICT.read_text(encoding="utf-8")) if FRAG_DICT.exists() else {}
    for p in [*SITE.rglob("*.html"), *SITE.glob("*.js")]:   # the code's own pairs need no entry
        for m in PAIR.finditer(p.read_text(encoding="utf-8")):
            have.setdefault(norm(m.group(1)), m.group(2))
    uhave = json.loads(UNIT_DICT.read_text(encoding="utf-8")) if UNIT_DICT.exists() else {}
    bad = [k for k in units if uhave.get(k) and markers(k) != markers(uhave[k])]
    for k in bad:
        print("  markers differ, ignored:", k)
    uout = {k: uhave[k] for k in sorted(units) if uhave.get(k) and k not in bad}
    fout = {k: have[k] for k in sorted(frags) if have.get(k)}
    umiss = sorted(k for k in units if k not in uout)
    fmiss = sorted(k for k in frags if k not in fout)
    j = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    (SITE / "i18n_en.js").write_text(
        "/* generated by scripts/i18n_build.py: Vietnamese -> English for site/i18n.js. Do not edit by hand. */\n"
        f"window.WD_I18N_UNITS={j(uout)};\nwindow.WD_I18N_EN={j(fout)};\n"
        "window.WD_I18N && WD_I18N.setup && WD_I18N.setup();\n", encoding="utf-8", newline="\n")
    # cache-busting: i18n.js loads i18n_en.js?v=<hash of its content>

    ver = hashlib.sha1((SITE / "i18n_en.js").read_bytes()).hexdigest()[:10]
    js = (SITE / "i18n.js").read_text(encoding="utf-8")
    js2 = re.sub(r"const DICT_V = '[^']*';", f"const DICT_V = '{ver}';", js)
    if js2 != js:
        (SITE / "i18n.js").write_text(js2, encoding="utf-8", newline="\n")
    print(f"{len(uout)} units, {len(fout)} fragments; missing {len(umiss)} units, {len(fmiss)} fragments")
    if "--dump" in sys.argv:
        (ROOT / "scripts" / "i18n_missing_units.json").write_text(json.dumps(umiss, ensure_ascii=False, indent=1), encoding="utf-8")
        (ROOT / "scripts" / "i18n_missing.json").write_text(json.dumps(fmiss, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in (umiss + fmiss)[:30]:
        print("  missing:", k)
    return 1 if (umiss or fmiss or bad) and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
