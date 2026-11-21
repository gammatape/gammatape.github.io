/* Wyckdelta site VI / EN (2026-11-20). The page is written in Vietnamese; when the language is EN this layer
   translates what reaches the screen: DOM text and the title / placeholder / aria-label / alt attributes (a
   MutationObserver catches later renders) and document.title. The dictionary (window.WD_I18N_EN, i18n_en.js, built by
   scripts/i18n_build.py) maps every Vietnamese fragment found in the pages and scripts to English; dynamic strings are
   translated fragment by fragment, longest first. Same design as the Tuong Chart app (js/i18n.js there).
   Language: ?lang=en / ?lang=vi in the URL wins and is remembered; otherwise localStorage "wd-lang"; default VI.
   Switching reloads the page. Elements with data-i18n-skip are never translated (news text, language names). */
(() => {
'use strict';
const KEY = 'wd-lang';
const DICT_V = '21bce860fd';  // i18n_en.js version, written by scripts/i18n_build.py
function readLang() {
  try {
    const q = new URLSearchParams(location.search).get('lang');
    if (q) { const l = q.toLowerCase() === 'en' ? 'EN' : 'VI'; localStorage.setItem(KEY, l); return l; }
  } catch (e) { /* no storage */ }
  try { return localStorage.getItem(KEY) === 'EN' ? 'EN' : 'VI'; } catch (e) { return 'VI'; }
}
const LANG = readLang();
const VI_RE = /[ăâđêôơưĂÂĐÊÔƠƯàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵÀÁẢÃẠẰẮẲẴẶẦẤẨẪẬÈÉẺẼẸỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌỒỐỔỖỘỜỚỞỠỢÙÚỦŨỤỪỨỬỮỰỲÝỶỸỴ]/;
const API = window.WD_I18N = {
  lang: LANG, en: LANG === 'EN', locale: LANG === 'EN' ? 'en-US' : 'vi-VN', missing: new Set(),
  t: (vi, en) => (LANG === 'EN' ? en : vi), tr: s => s,
};
document.documentElement.lang = LANG === 'EN' ? 'en' : 'vi';

API.setLang = l => {
  l = l === 'EN' ? 'EN' : 'VI';
  try { localStorage.setItem(KEY, l); } catch (e) { /* blocked */ }
  const u = new URL(location.href);
  if (u.searchParams.has('lang')) u.searchParams.set('lang', l.toLowerCase());
  if (u.href !== location.href) location.href = u.href; else location.reload();
};
// every element with [data-lang-switch] becomes a VI | EN toggle
function wire() {
  for (const b of document.querySelectorAll('[data-lang-switch]')) {
    b.setAttribute('data-i18n-skip', '');
    for (const o of b.querySelectorAll('[data-l]')) {
      o.setAttribute('aria-pressed', String(o.dataset.l === LANG));
      o.onclick = () => { if (o.dataset.l !== LANG) API.setLang(o.dataset.l); };
    }
  }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire); else wire();

if (LANG !== 'EN') return;
// The dictionary is loaded only for English readers; i18n_en.js calls WD_I18N.setup() once it has run.
let ready = false;
API.setup = () => { if (!ready && window.WD_I18N_EN) { ready = true; setup(); } };
if (window.WD_I18N_EN) API.setup(); else document.write('<script src="i18n_en.js?v=' + DICT_V + '"><\/script>');

function setup() {
const DICT = new Map();
for (const [k, v] of Object.entries(window.WD_I18N_EN || {})) {
  if (typeof v !== 'string' || !v) continue;
  DICT.set(k, v);
  const t = k.trim();
  if (t && t !== k && !DICT.has(t)) DICT.set(t, v.trim());
  const up = k.toUpperCase();
  if (up !== k && !DICT.has(up)) DICT.set(up, v.toUpperCase());
}
const keys = [...DICT.keys()].map(k => k.trim()).filter((k, i, a) => k && VI_RE.test(k) && a.indexOf(k) === i)
  .sort((a, b) => b.length - a.length);
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// a fragment never starts or ends inside a word; fragments that start / end with punctuation (": chi tiết") may touch one
const LN = /[\p{L}\p{N}]/u;
const fragRe = behind => new RegExp(keys.map(k => (behind && LN.test(k[0]) ? '(?<![\\p{L}\\p{N}])' : '') + esc(k) +
  (LN.test(k[k.length - 1]) ? '(?![\\p{L}\\p{N}])' : '')).join('|'), 'gu');
let FRAG = null;
// Safari before 16.4 has no lookbehind: fall back to the end-of-word check only
if (keys.length) { try { FRAG = fragRe(true); } catch (e) { FRAG = fragRe(false); } }
const cache = new Map();
function tr(s) {
  if (typeof s !== 'string' || !s || !VI_RE.test(s)) return s;
  let r = cache.get(s);
  if (r !== undefined) return r;
  r = DICT.get(s);
  if (r === undefined) {
    // HTML source text carries line breaks and indentation: look it up with whitespace collapsed, keep the edges
    const t = s.replace(/\s+/g, ' ').trim(), d = DICT.get(t);
    if (d !== undefined) r = (/^\s/.test(s) ? ' ' : '') + d + (/\s$/.test(s) ? ' ' : '');
  }
  if (r === undefined && FRAG) r = s.replace(/\s+/g, ' ').replace(FRAG, m => { const v = DICT.get(m); return v !== undefined ? v : m; });
  if (r === undefined) r = s;
  if (VI_RE.test(r)) API.missing.add(s.length > 200 ? s.slice(0, 200) : s);
  if (cache.size > 20000) cache.clear();
  cache.set(s, r);
  return r;
}
API.tr = tr;

// ---- units: a whole block whose children are only inline elements, translated as one sentence.
// Key = text with each inline element as a marker ({0}…{/0}, void ones {1/}); must match scripts/i18n_build.py.
const UNITS = window.WD_I18N_UNITS || {};
const INLINE = new Set(['A', 'B', 'STRONG', 'I', 'EM', 'SPAN', 'SMALL', 'CODE', 'KBD', 'SUP', 'SUB', 'MARK', 'U', 'S', 'TIME', 'ABBR']);
const ATOMIC = new Set(['BR', 'IMG', 'SVG', 'WBR', 'svg']);
const SKIP_TAGS_U = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'PRE', 'TEMPLATE', 'NOSCRIPT']);
const isSkip = n => SKIP_TAGS_U.has(n.tagName) || n.hasAttribute('data-i18n-skip') || n.getAttribute('translate') === 'no';
function onlyInline(el) {
  for (const c of el.children) {
    if (isSkip(c)) return false;
    if (ATOMIC.has(c.tagName)) continue;          // <br>, <img>, <svg>: kept whole
    if (!INLINE.has(c.tagName) || !onlyInline(c)) return false;
  }
  return true;
}
function unitKey(el, nodes) {
  const rec = node => {
    let s = '';
    for (const c of node.childNodes) {
      if (c.nodeType === 3) s += c.nodeValue;
      else if (c.nodeType === 1) {
        const i = nodes.length; nodes.push(c);
        s += ATOMIC.has(c.tagName) ? `{${i}/}` : `{${i}}${rec(c)}{/${i}}`;
      }
    }
    return s;
  };
  return rec(el).replace(/\s+/g, ' ').trim();
}
// rebuild the children from the English template, moving the original inline elements (ids, listeners kept)
function applyUnit(el, en, nodes) {
  const parts = en.split(/(\{\/?\d+\/?\})/);
  const stack = [document.createDocumentFragment()];
  for (const p of parts) {
    let m;
    if (!p) continue;
    if ((m = p.match(/^\{(\d+)\/\}$/))) stack[stack.length - 1].append(nodes[+m[1]]);
    else if ((m = p.match(/^\{(\d+)\}$/))) { const n = nodes[+m[1]]; n.replaceChildren(); stack[stack.length - 1].append(n); stack.push(n); }
    else if (/^\{\/\d+\}$/.test(p)) { if (stack.length > 1) stack.pop(); }
    else stack[stack.length - 1].append(document.createTextNode(p));
  }
  el.replaceChildren(stack[0]);
}
function tryUnit(el) {
  if (el.tagName === 'HTML' || el.tagName === 'HEAD' || el.tagName === 'BODY' || ATOMIC.has(el.tagName)) return false;
  if (!VI_RE.test(el.textContent) || !onlyInline(el)) return false;
  const nodes = [], k = unitKey(el, nodes), en = UNITS[k];
  if (en === undefined) return false;
  applyUnit(el, en, nodes);
  return true;
}

const ATTRS = ['title', 'placeholder', 'aria-label', 'alt', 'content'];
const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'CODE', 'PRE']);
function skip(el) {
  for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
    if (SKIP_TAGS.has(e.tagName) || e.hasAttribute('data-i18n-skip') || e.getAttribute('translate') === 'no') return true;
  }
  return false;
}
function doText(n) {
  const v = n.nodeValue;
  if (!v || !VI_RE.test(v)) return;
  if (n.parentElement && skip(n.parentElement)) return;
  const t = tr(v);
  if (t !== v) n.nodeValue = t;
}
function doAttrs(el) {
  if (el.closest && el.closest('[data-i18n-skip]')) return;
  for (const a of ATTRS) {
    if (a === 'content' && el.tagName !== 'META') continue;
    const v = el.getAttribute(a);
    if (v && VI_RE.test(v)) { const t = tr(v); if (t !== v) el.setAttribute(a, t); }
  }
}
// whole-sentence units first; what is left goes fragment by fragment
function visit(el) {
  if (SKIP_TAGS.has(el.tagName) || el.hasAttribute('data-i18n-skip') || el.getAttribute('translate') === 'no') return;
  doAttrs(el);
  if (tryUnit(el)) { for (const d of el.querySelectorAll('*')) doAttrs(d); return; }
  for (const c of [...el.childNodes]) {
    if (c.nodeType === 3) doText(c);
    else if (c.nodeType === 1) visit(c);
  }
}
function walk(root) {
  if (root.nodeType === 3) { doText(root); return; }
  if (root.nodeType === 9) root = root.documentElement;
  if (root.nodeType !== 1 || (root.parentElement && skip(root.parentElement))) return;
  visit(root);
}
new MutationObserver(list => {
  for (const m of list) {
    if (m.type === 'childList') { for (const n of m.addedNodes) walk(n); }
    else if (m.type === 'characterData') doText(m.target);
    else if (m.type === 'attributes' && m.target.nodeType === 1) doAttrs(m.target);
  }
}).observe(document.documentElement, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
const first = () => { walk(document.documentElement); if (VI_RE.test(document.title)) document.title = tr(document.title); };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', first); else first();
}
})();
