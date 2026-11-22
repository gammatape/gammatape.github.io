"""Build every page of wyckdelta.com from one shell (2026-11-22).

The site used to be one long page. It is now split into sections with their own URLs, like the big finance portals:
a left rail of sections (icon + label); hovering or focusing a section opens a flyout with its sub-pages; on a phone
the rail is a drawer where each section unfolds, plus a bottom tab bar. Every section page has a row of sub-page
tabs under the header and a breadcrumb.

Sources (edit these, then run this script; the HTML under site/ is generated):
  scripts/site_src/cards.html     the data cards (one <section class="card" id=...> each), drawn by site/app.js
  scripts/site_src/hero.html      home hero
  scripts/site_src/features.html  Wyckdelta Chart features
  scripts/site_src/lessons.html   the four lessons (<details class="lesson">)
  scripts/site_src/final.html     closing call to action
  scripts/site_src/footer.html    footer
  this file                       navigation, page list, page text (articles)

    py -B scripts/build_pages.py           # write the pages
    py -B scripts/build_pages.py --check   # exit 1 when a page under site/ differs from what this script writes

Then run scripts/i18n_build.py so new Vietnamese text gets its English.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SRC = ROOT / "scripts" / "site_src"
BASE = "https://wyckdelta.com"
INBOX = "https://m.me/61596278051545?ref=wyckdelta_web"


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def ver(*files):
    h = hashlib.sha1()
    for f in files:
        h.update((SITE / f).read_bytes())
    return h.hexdigest()[:8]


# ------------------------------------------------------------------ icons (24x24 stroke paths)
ICON = {
    "home": '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "market": '<path d="M4 19V5M4 19h16M8 15l3-4 3 2 5-6"/>',
    "position": '<path d="M5 20V10M11 20V4M17 20v-8M3 20h18"/>',
    "macro": '<path d="M3 10l9-6 9 6M5 10v9M9.5 10v9M14.5 10v9M19 10v9M3 21h18"/>',
    "news": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/>',
    "learn": '<path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2zM20 19v2H6"/>',
    "chart": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M7 14l3-3 2 2 5-5M8 21h8"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "chev": '<path d="M9 6l6 6-6 6"/>',
    "down": '<path d="M6 9l6 6 6-6"/>',
}


def svg(name, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} viewBox="0 0 24 24" aria-hidden="true">{ICON[name]}</svg>'


# ------------------------------------------------------------------ navigation: section -> sub-pages
# (key, label, url, icon, [(label, url, short description for the section directory)])
NAV = [
    ("home", "Trang chủ", "/", "home", []),
    ("thi-truong", "Thị trường", "/thi-truong/", "market", [
        ("Tổng quan", "/thi-truong/", "Sáu mã trên một màn hình"),
        ("Vàng", "/thi-truong/vang/", "COT, quỹ GLD, lợi suất thực"),
        ("S&P 500 · Nasdaq", "/thi-truong/chung-khoan-my/", "Vị thế quỹ lớn ES, NQ"),
        ("Dầu WTI", "/thi-truong/dau/", "COT, tồn kho EIA"),
        ("Crypto", "/thi-truong/crypto/", "Giá, tâm lý, vị thế CME"),
    ]),
    ("vi-the", "Vị thế", "/vi-the/", "position", [
        ("Tổng quan", "/vi-the/", "Ai đang nắm giữ gì"),
        ("Quỹ lớn (COT)", "/vi-the/cot/", "Vị thế ròng 52 tuần"),
        ("Ai mua, ai bán", "/vi-the/ai-mua-ai-ban/", "Quỹ, nhà sản xuất, ngân hàng"),
        ("Ai đang đông người", "/vi-the/dong-nguoi/", "COT Index 0–100"),
        ("Quỹ vàng GLD", "/vi-the/quy-vang-gld/", "Số tấn vàng quỹ đang giữ"),
    ]),
    ("vi-mo", "Vĩ mô", "/vi-mo/", "macro", [
        ("Tổng quan", "/vi-mo/", "Lịch tin, lãi suất, dầu"),
        ("Lịch tin tuần", "/vi-mo/lich-tin/", "Tin USD theo giờ VN"),
        ("Lợi suất Mỹ", "/vi-mo/loi-suat/", "Đường cong trái phiếu"),
        ("Chỉ số vĩ mô Mỹ", "/vi-mo/chi-so/", "Lợi suất thực, EFFR"),
        ("Tồn kho dầu", "/vi-mo/ton-kho-dau/", "Báo cáo EIA thứ Tư"),
    ]),
    ("tin-tuc", "Tin tức", "/tin-tuc/", "news", [
        ("Tin liên quan", "/tin-tuc/", "Mọi tin về các mã đang theo dõi"),
        ("Vàng", "/tin-tuc/vang/", "Tin vàng"),
        ("S&P · Nasdaq", "/tin-tuc/chung-khoan/", "Tin chứng khoán Mỹ"),
        ("Dầu", "/tin-tuc/dau/", "Tin dầu"),
        ("Crypto", "/tin-tuc/crypto/", "Tin crypto"),
        ("Fed & vĩ mô", "/tin-tuc/fed/", "Fed, lạm phát, việc làm"),
        ("Nguồn chính thức", "/tin-tuc/chinh-thuc/", "Fed, EIA, CFTC"),
    ]),
    ("hoc", "Học", "/hoc/", "learn", [
        ("Tất cả bài học", "/hoc/", "Bốn khái niệm nền"),
        ("Footprint", "/hoc/footprint/", "Bid/ask tại từng mức giá"),
        ("Delta & CVD", "/hoc/delta-cvd/", "Lệnh chủ động mua/bán"),
        ("Volume Profile", "/hoc/volume-profile/", "POC, Value Area"),
        ("Báo cáo COT", "/hoc/cot/", "Đọc vị thế quỹ lớn"),
    ]),
    ("wyckdelta-chart", "Wyckdelta Chart", "/wyckdelta-chart/", "chart", [
        ("Tính năng", "/wyckdelta-chart/", "Order flow + GEX trên một biểu đồ"),
        ("Cài đặt app", "/huong-dan.html", "Windows, điện thoại, Mac"),
        ("Mở Wyckdelta Chart", "/chart.html", "Đã có tài khoản"),
    ]),
]
SECTION = {k: (label, url, subs) for k, label, url, _i, subs in NAV}
TABBAR = [("thi-truong", "Thị trường", "market"), ("vi-the", "Vị thế", "position"), ("vi-mo", "Vĩ mô", "macro"),
          ("tin-tuc", "Tin tức", "news")]


def rail(cat):
    out = []
    for i, (k, label, url, icon, subs) in enumerate(NAV):
        on = ' aria-current="true"' if k == cat else ""
        fly = ""
        if subs:
            up = " up" if i >= 4 else ""   # lower sections open upwards so long lists stay on screen
            links = "".join(f'<a href="{u}">{l}</a>' for l, u, _d in subs)
            fly = (f'<button class="ri-tog" type="button" aria-expanded="{str(k == cat).lower()}" aria-label="Mở mục {label}">'
                   f'{svg("down")}</button>'
                   f'<div class="fly{up}"><p class="fly-h">{label}</p>{links}</div>')
        out.append(f'<div class="ri{" open" if k == cat else ""}" data-cat="{k}"><a class="rl" href="{url}"{on}>'
                   f'{svg(icon)}<span>{label}</span></a>{fly}</div>')
    return "\n    ".join(out)


def subnav(cat, path):
    label, url, subs = SECTION[cat]
    if not subs:
        return ""
    items = []
    for l, u, _d in subs:
        cur = ' aria-current="page"' if u == path else ""
        items.append(f'<a href="{u}"{cur}>{l}</a>')
    return f'<nav class="subnav" aria-label="{label}"><div class="subnav-in">{"".join(items)}</div></nav>'


def crumbs(cat, path, title):
    if cat == "home":
        return ""
    label, url, _s = SECTION[cat]
    parts = ['<a href="/">Trang chủ</a>']
    if path != url:
        parts.append(f'<a href="{url}">{label}</a>')
        parts.append(f'<span aria-current="page">{title}</span>')
    else:
        parts.append(f'<span aria-current="page">{label}</span>')
    return '<nav class="crumbs" aria-label="Đường dẫn">' + '<span class="sep" aria-hidden="true">›</span>'.join(parts) + "</nav>"


# ------------------------------------------------------------------ building blocks
def cards():
    text = read("cards.html")
    out = {}
    for m in re.finditer(r'(<section class="card[^"]*" id="([a-z-]+)".*?</section>)', text, re.S):
        out[m.group(2)] = m.group(1)
    return out


CARDS = cards()


COT_Q = "Vị thế ròng 52 tuần của 6 mã. Thanh dưới mỗi thẻ là COT Index 26 tuần: hai đầu tô màu là vùng đã đông người. Bấm một mã để xem kịch bản."
COT_Q2 = "Vị thế ròng 52 tuần của 2 mã. Thanh dưới mỗi thẻ là COT Index 26 tuần: hai đầu tô màu là vùng đã đông người. Bấm một mã để xem kịch bản."
COT_Q1 = "Vị thế ròng 52 tuần. Thanh dưới thẻ là COT Index 26 tuần: hai đầu tô màu là vùng đã đông người."


def card(cid, full=False, open_cal=False, cls=None, one=False, two=False):
    h = CARDS[cid]
    if one or two:   # a page about one / two markets: the COT card shows only those
        assert COT_Q in h
        h = h.replace(COT_Q, COT_Q1 if one else COT_Q2)
    if full:
        h = h.replace('class="card', 'class="card full', 1)
    if cls:
        h = h.replace('class="card', f'class="card {cls}', 1)
    if open_cal:
        h = h.replace('<details class="full" id="cal-full">', '<details class="full" id="cal-full" open>')
    return h


def grid(*items):
    return '<div class="grid">\n' + "\n".join(items) + "\n</div>"


def article(title, body, kicker="Cách đọc chuyên sâu"):
    return (f'<section class="article"><span class="kicker">{kicker}</span><h2>{title}</h2>\n{body}\n</section>')


def related(*links):
    a = "".join(f'<a class="rel" href="{u}"><b>{t}</b><span>{d}</span>{svg("chev")}</a>' for t, u, d in links)
    return f'<section class="related"><h2>Xem thêm</h2><div class="rel-grid">{a}</div></section>'


def directory(keys=None):
    """Section directory: one tile per section with its sub-pages (home page and section overviews)."""
    tiles = []
    for k, label, url, icon, subs in NAV:
        if not subs or (keys and k not in keys):
            continue
        links = "".join(f'<li><a href="{u}">{l}</a><span>{d}</span></li>' for l, u, d in subs if u != url)
        tiles.append(f'<div class="dir"><a class="dir-h" href="{url}">{svg(icon)}<b>{label}</b>{svg("chev", "go")}</a>'
                     f'<ul>{links}</ul></div>')
    return f'<section class="directory"><h2>Khám phá theo mục</h2><div class="dir-grid">{"".join(tiles)}</div></section>'


def lessons():
    text = read("lessons.html")
    return re.findall(r'(<details class="lesson">.*?</details>)', text, re.S)


LESSONS = lessons()


def lesson_page(i):
    """A lesson as a full page: the <details> opened into an article."""
    h = LESSONS[i]
    title = re.search(r"<summary>(.*?)</summary>", h).group(1)
    lead = re.search(r'<p class="lead">(.*?)</p>', h).group(1)
    body = re.search(r'<div class="body">(.*?)</div>', h, re.S).group(1)
    return title, lead, body


def ul(*items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


DISCLAIMER = '<p class="note">Nội dung mang tính giáo dục, không phải lời khuyên đầu tư hay khuyến nghị mua bán.</p>'

# ------------------------------------------------------------------ deep-dive text per page
WATCH = {
    "GC": article("Điều cần theo dõi với Vàng", ul(
        "<b>Lợi suất thực 10 năm</b> (TIPS): vàng không trả lãi, nên lợi suất thực giảm thường hỗ trợ vàng, tăng thường gây áp lực.",
        "<b>Đồng USD</b>: vàng định giá bằng USD; USD mạnh lên thường làm vàng đắt hơn với người mua ngoài Mỹ.",
        "<b>Dòng tiền quỹ ETF</b> (GLD): số tấn quỹ giữ tăng nghĩa là nhà đầu tư đang rót tiền vào vàng.",
        "<b>Vị thế quỹ lớn (COT)</b>: COT Index gần 100 nghĩa là phía mua đã đông, dễ rung lắc khi có tin xấu.",
        "<b>Tin đỏ USD</b>: CPI, NFP, quyết định lãi suất Fed thường làm vàng biến động mạnh trong vài phút đầu.",
    ) + DISCLAIMER, "Bối cảnh"),
    "ES NQ": article("Điều cần theo dõi với S&P 500 và Nasdaq", ul(
        "<b>Lãi suất và lợi suất</b>: lợi suất dài hạn tăng nhanh thường gây áp lực lên cổ phiếu tăng trưởng, Nasdaq nhạy hơn S&P 500.",
        "<b>Tin lạm phát và việc làm</b>: CPI, PCE, NFP làm thay đổi kỳ vọng lãi suất của Fed.",
        "<b>Vị thế quỹ lớn (COT)</b>: COT của ES, NQ gồm cả vị thế phòng hộ của quỹ, nên đọc cùng xu hướng giá, không đọc riêng.",
        "<b>Mùa báo cáo lợi nhuận</b> của các công ty lớn nhóm công nghệ chi phối Nasdaq 100.",
    ) + DISCLAIMER, "Bối cảnh"),
    "CL": article("Điều cần theo dõi với Dầu WTI", ul(
        "<b>Tồn kho dầu thô EIA</b> (thứ Tư, khoảng 21:30 giờ VN): giảm thường được đọc là cầu mạnh; số liệu API tối thứ Ba đi trước.",
        "<b>Xăng và dầu chưng cất</b>: tồn kho sản phẩm cho biết nhu cầu tiêu dùng cuối cùng.",
        "<b>Quyết định sản lượng của OPEC+</b> và tin địa chính trị ở vùng sản xuất.",
        "<b>Quỹ đầu cơ (Managed Money)</b>: vị thế ròng đổi chiều nhanh thường đi cùng các nhịp giá mạnh.",
    ) + DISCLAIMER, "Bối cảnh"),
    "BTC ETH": article("Điều cần theo dõi với Crypto", ul(
        "<b>Chỉ số Sợ hãi &amp; Tham lam</b>: ở hai đầu (dưới 25, trên 75) tâm lý đã cực đoan.",
        "<b>Vị thế trên CME</b>: COT của Bitcoin, Ether trên CME phản ánh quỹ và tổ chức, không phải toàn bộ thị trường crypto.",
        "<b>Lãi suất và đồng USD</b>: crypto thường nhạy với thay đổi kỳ vọng lãi suất của Fed như cổ phiếu công nghệ.",
        "<b>Crypto giao dịch 24/7</b>: biến động lớn hay xảy ra cuối tuần khi thanh khoản mỏng.",
    ) + DISCLAIMER, "Bối cảnh"),
}

ART = {
    "cot": article("Đọc báo cáo COT thế nào", ul(
        "CFTC chốt số liệu vị thế mỗi <b>thứ Ba</b>, công bố <b>thứ Sáu</b> (khoảng 02:30 sáng thứ Bảy giờ VN), nên luôn trễ 3 ngày.",
        "<b>Non-commercial</b> (quỹ đầu cơ lớn) thường đi theo xu hướng; <b>Commercial</b> (nhà sản xuất, người phòng hộ) thường đi ngược giá.",
        "<b>COT Index</b> = vị trí của vị thế ròng hiện tại trong biên thấp nhất–cao nhất 26 tuần (hoặc 3 năm): 0 là thấp nhất, 100 là cao nhất.",
        "Vị thế ở vùng cực đoan không phải tín hiệu vào lệnh; nó cho biết phía nào đã đông người và dễ bị ép khi giá đi ngược.",
    ) + DISCLAIMER),
    "flows": article("Ba nhóm trên sàn hàng hoá", ul(
        "<b>Quỹ đầu cơ (Managed Money)</b>: CTA, quỹ phòng hộ; thường mua khi giá tăng và bán khi giá giảm.",
        "<b>Nhà sản xuất, thương nhân (Producer/Merchant)</b>: mỏ vàng, nhà lọc dầu, nhà buôn; bán khống để khoá giá bán, nên vị thế ròng thường âm.",
        "<b>Ngân hàng (Swap Dealer)</b>: đứng giữa để làm hợp đồng hoán đổi cho khách, rồi phòng hộ trên sàn.",
        "Đáng chú ý nhất là khi quỹ đầu cơ đổi chiều nhanh trong vài tuần liên tiếp.",
    ) + DISCLAIMER),
    "crowd": article("Vì sao vùng đông người dễ đảo chiều", ul(
        "Khi gần như mọi quỹ đã mua, còn rất ít người mua mới để đẩy giá đi tiếp.",
        "Một tin xấu có thể khiến nhiều quỹ cùng chốt lời một lúc, làm giá giảm nhanh hơn bình thường.",
        "Chấm vàng (26 tuần) cho biết bối cảnh gần; vòng tròn (3 năm) cho biết bối cảnh dài. Cả hai cùng ở một đầu thì vùng cực đoan rõ hơn.",
        "Vị thế có thể ở vùng cực đoan nhiều tuần liền khi xu hướng mạnh; dùng nó để quản lý rủi ro, không để đoán đỉnh đáy.",
    ) + DISCLAIMER),
    "gld": article("Quỹ vàng GLD nói gì", ul(
        "Mỗi cổ phiếu GLD được bảo chứng bằng vàng vật chất trong kho, nên số tấn quỹ giữ đi theo dòng tiền vào / ra.",
        "Số tấn tăng nhiều phiên liên tiếp: nhà đầu tư phương Tây đang mua vàng qua quỹ.",
        "Dòng tiền quỹ thường đi cùng xu hướng giá, không báo trước giá. Ngân hàng trung ương và nhu cầu châu Á không nằm trong con số này.",
    ) + DISCLAIMER),
    "calendar": article("Tin nào làm thị trường chạy mạnh", ul(
        "<b>Bảng lương phi nông nghiệp (NFP)</b>: thứ Sáu đầu tháng, 19:30 hoặc 20:30 giờ VN tuỳ giờ mùa hè / mùa đông ở Mỹ.",
        "<b>CPI</b>: giữa tháng, cùng giờ NFP; lạm phát cao hơn dự báo thường đẩy lợi suất và USD lên.",
        "<b>Quyết định lãi suất Fed (FOMC)</b>: 8 lần một năm, khoảng 01:00–02:00 sáng giờ VN, kèm họp báo 30 phút sau.",
        "Chấm đỏ là tin ảnh hưởng cao: giá có thể giật mạnh và chênh lệch giá mua / bán giãn ra trong vài phút đầu.",
    ) + DISCLAIMER),
    "curve": article("Đọc đường cong lợi suất", ul(
        "Bình thường đường cong <b>dốc lên</b>: cho vay càng lâu đòi lãi càng cao.",
        "<b>Đảo ngược</b> (kỳ hạn ngắn cao hơn kỳ hạn dài) cho thấy thị trường chờ Fed hạ lãi suất; trong lịch sử thường đi trước suy thoái.",
        "Chênh <b>10 năm − 2 năm</b> và <b>10 năm − 3 tháng</b> là hai thước đo hay dùng nhất.",
        "Đường cong dốc lên trở lại sau một thời gian dài đảo ngược cũng là lúc cần chú ý.",
    ) + DISCLAIMER),
    "macro": article("Các chỉ số vĩ mô ở đây", ul(
        "<b>Lợi suất danh nghĩa 10 năm</b>: chi phí vay dài hạn của chính phủ Mỹ.",
        "<b>Lợi suất thực 10 năm</b> (TIPS): lợi suất sau khi trừ lạm phát kỳ vọng, chỉ số quan trọng nhất với vàng.",
        "<b>Lạm phát kỳ vọng (breakeven)</b> = lợi suất danh nghĩa − lợi suất thực.",
        "<b>EFFR</b>: lãi suất qua đêm thực tế giữa các ngân hàng, bám sát biên lãi suất Fed đặt ra.",
    ) + DISCLAIMER),
    "eia": article("Đọc báo cáo tồn kho EIA", ul(
        "EIA công bố thứ Tư (khoảng 21:30 giờ VN, lệch một giờ theo giờ mùa ở Mỹ) cho tuần kết thúc thứ Sáu trước đó.",
        "So sánh với dự báo của thị trường quan trọng hơn con số tuyệt đối.",
        "Tồn kho dầu thô ở Cushing (điểm giao WTI) ảnh hưởng trực tiếp tới giá hợp đồng WTI.",
        "Tồn kho xăng giảm vào mùa lái xe (hè ở Mỹ) là chuyện thường; cần so với cùng kỳ năm trước.",
    ) + DISCLAIMER),
    "crypto": article("Đọc trang crypto", ul(
        "Giá là giá tham khảo tổng hợp từ nhiều sàn, cập nhật mỗi 30 phút, không dùng để đặt lệnh.",
        "Chỉ số Sợ hãi &amp; Tham lam gộp biến động, khối lượng, mạng xã hội và tỷ trọng Bitcoin thành một con số 0–100.",
        "Vị thế COT của Bitcoin, Ether lấy từ hợp đồng tương lai trên CME.",
    ) + DISCLAIMER),
}


# ------------------------------------------------------------------ the page list
def P(path, cat, title, h1, desc, body, *, intro="", kicker="", data=True, ticker=False, pulse=False,
      note=False, hero=False, fold=False, assets="", news="", final=True):
    return dict(path=path, cat=cat, title=title, h1=h1, desc=desc, body=body, intro=intro, kicker=kicker, data=data,
                ticker=ticker, pulse=pulse, note=note, hero=hero, fold=fold, assets=assets, news=news, final=final)


def asset_page(path, title, h1, intro, assets, news, extra):
    rel = [("Vị thế quỹ lớn", "/vi-the/cot/", "Cả 6 mã"), ("Lịch tin tuần", "/vi-mo/lich-tin/", "Tin USD giờ VN"),
           ("Tin tức", news_url(news), "Tin của mã này")]
    return P(path, "thi-truong", title, h1, intro, grid(*extra) + WATCH[assets] + related(*rel),
             intro=intro, kicker="Thị trường", assets=assets, news=news, ticker=True)


def news_url(topics):
    return {"GC": "/tin-tuc/vang/", "ES NQ": "/tin-tuc/chung-khoan/", "CL": "/tin-tuc/dau/", "CRYPTO": "/tin-tuc/crypto/"}.get(topics, "/tin-tuc/")


def news_page(path, title, h1, intro, topics):
    return P(path, "tin-tuc", title, h1, intro, grid(card("news", full=True)), intro=intro, kicker="Tin tức", news=topics)


def lesson(path, i, rel):
    title, lead, body = lesson_page(i)
    return P(path, "hoc", title, title, lead,
             f'<section class="article lesson-body"><p class="lead">{lead}</p>\n{body}\n</section>' + related(*rel),
             intro="", kicker="Học", data=False)


PAGES = [
    P("/", "home", "Wyckdelta · Order flow + GEX, nhịp thị trường mỗi ngày", "Nhịp thị trường hôm nay",
      "Wyckdelta Chart: footprint, heatmap sổ lệnh, iceberg và các mức GEX trên một biểu đồ cho Vàng, ES, NQ, crypto. "
      "Kèm nhịp thị trường miễn phí: COT, tồn kho dầu, vĩ mô, lịch kinh tế, tin tức.",
      grid(card("cot"), card("calendar"), card("macro"), card("crypto"), card("crowd")) + directory(),
      intro="Vàng, ES, NQ, dầu, BTC, ETH: quỹ lớn, vĩ mô, lịch tin. Tự cập nhật mỗi 30 phút. Mỗi mục có trang riêng ở menu bên trái.",
      kicker="Miễn phí cho tất cả", ticker=True, pulse=True, note=True, hero=True, fold=True),

    # ---- Thị trường
    P("/thi-truong/", "thi-truong", "Thị trường hôm nay", "Thị trường hôm nay",
      "Sáu mã trên một màn hình: vị thế quỹ lớn, kịch bản, crypto và vùng đông người.",
      grid(card("cot"), card("crypto"), card("crowd")) + directory(["thi-truong"]),
      intro="Sáu mã trên một màn hình. Bấm một mã để xem kịch bản, hoặc mở trang riêng của mã ở thanh mục phía trên.",
      kicker="Thị trường", ticker=True, pulse=True, fold=True),
    asset_page("/thi-truong/vang/", "Vàng (GC) hôm nay", "Vàng · GC",
               "Quỹ lớn, quỹ vàng GLD, ba nhóm trên sàn và vĩ mô tác động lên vàng, trên một trang.",
               "GC", "GC", [card("cot", full=True, one=True), card("gld", full=True), card("flows"), card("macro")]),
    asset_page("/thi-truong/chung-khoan-my/", "S&P 500 và Nasdaq 100 hôm nay", "S&P 500 · Nasdaq 100",
               "Vị thế quỹ lớn trên hợp đồng ES, NQ, lợi suất Mỹ và lịch tin trong tuần.",
               "ES NQ", "ES NQ", [card("cot", full=True, two=True), card("loi-suat"), card("macro"), card("calendar", full=True)]),
    asset_page("/thi-truong/dau/", "Dầu WTI (CL) hôm nay", "Dầu WTI · CL",
               "Quỹ lớn, ba nhóm trên sàn và tồn kho dầu Mỹ của EIA.",
               "CL", "CL", [card("cot", full=True, one=True), card("flows"), card("eia")]),
    asset_page("/thi-truong/crypto/", "Crypto hôm nay", "Crypto · BTC, ETH",
               "Giá, chỉ số Sợ hãi & Tham lam và vị thế quỹ lớn trên hợp đồng Bitcoin, Ether của CME.",
               "BTC ETH", "CRYPTO", [card("crypto", full=True), card("cot", full=True, two=True)]),

    # ---- Vị thế
    P("/vi-the/", "vi-the", "Vị thế quỹ lớn", "Vị thế: ai đang nắm giữ gì",
      "Báo cáo COT của CFTC, ba nhóm trên sàn hàng hoá và quỹ vàng GLD.",
      grid(card("cot"), card("crowd"), card("flows"), card("gld", full=True)) + directory(["vi-the"]),
      intro="Báo cáo COT của CFTC, ba nhóm trên sàn hàng hoá và quỹ vàng GLD.", kicker="Vị thế", fold=True),
    P("/vi-the/cot/", "vi-the", "Quỹ lớn đang nghiêng về đâu (COT)", "Vị thế quỹ lớn (COT)",
      "Vị thế ròng 52 tuần và COT Index của Vàng, S&P 500, Nasdaq, Dầu, Bitcoin, Ether.",
      grid(card("cot", full=True)) + ART["cot"] + related(("Ai đang đông người", "/vi-the/dong-nguoi/", "Sáu mã trên thang 0–100"),
                                                          ("Bài học: báo cáo COT", "/hoc/cot/", "Kiến thức nền")),
      intro="Vị thế ròng 52 tuần của 6 mã, kèm COT Index và kịch bản để quan sát.", kicker="Vị thế"),
    P("/vi-the/ai-mua-ai-ban/", "vi-the", "Ai đang mua, ai đang bán (Vàng, Dầu)", "Ba nhóm trên sàn Vàng và Dầu",
      "Quỹ đầu cơ, nhà sản xuất và ngân hàng trên sàn Vàng và Dầu, theo báo cáo Disaggregated của CFTC.",
      grid(card("flows", full=True)) + ART["flows"] + related(("Quỹ lớn (COT)", "/vi-the/cot/", "Cả 6 mã"),
                                                             ("Vàng", "/thi-truong/vang/", "Trang riêng của Vàng"),
                                                             ("Dầu WTI", "/thi-truong/dau/", "Trang riêng của Dầu")),
      intro="Vị thế ròng của từng nhóm trên sàn Vàng và Dầu, theo tuần.", kicker="Vị thế"),
    P("/vi-the/dong-nguoi/", "vi-the", "Ai đang đông người (COT Index)", "COT Index của 6 mã",
      "COT Index 26 tuần và 3 năm của 6 mã trên một thang 0–100.",
      grid(card("crowd", full=True)) + ART["crowd"] + related(("Quỹ lớn (COT)", "/vi-the/cot/", "Chi tiết từng mã")),
      intro="COT Index của 6 mã trên một thang 0–100. Ở hai đầu là vùng dễ đảo chiều.", kicker="Vị thế"),
    P("/vi-the/quy-vang-gld/", "vi-the", "Quỹ vàng SPDR (GLD) mua hay bán", "Dòng tiền quỹ vàng GLD",
      "Số tấn vàng quỹ ETF vàng lớn nhất thế giới đang giữ, thay đổi mỗi phiên, 6 tháng.",
      grid(card("gld", full=True)) + ART["gld"] + related(("Vàng", "/thi-truong/vang/", "Mọi số liệu về vàng"),
                                                         ("Chỉ số vĩ mô Mỹ", "/vi-mo/chi-so/", "Lợi suất thực")),
      intro="Thước đo dòng tiền đầu tư vào vàng qua quỹ ETF.", kicker="Vị thế"),

    # ---- Vĩ mô
    P("/vi-mo/", "vi-mo", "Vĩ mô Mỹ hôm nay", "Vĩ mô Mỹ",
      "Lịch tin tuần theo giờ VN, đường cong lợi suất, lợi suất thực, EFFR và tồn kho dầu.",
      grid(card("calendar"), card("macro"), card("loi-suat"), card("eia")) + directory(["vi-mo"]),
      intro="Lịch tin tuần theo giờ VN, đường cong lợi suất, lợi suất thực, EFFR và tồn kho dầu.", kicker="Vĩ mô", fold=True),
    P("/vi-mo/lich-tin/", "vi-mo", "Lịch tin kinh tế tuần này (giờ VN)", "Lịch tin kinh tế tuần này",
      "Lịch tin USD trong tuần theo giờ Việt Nam: NFP, CPI, Fed, kèm dự báo và số trước.",
      grid(card("calendar", full=True, open_cal=True)) + ART["calendar"] +
      related(("Tin Fed & vĩ mô", "/tin-tuc/fed/", "Tin mới nhất"), ("Chỉ số vĩ mô Mỹ", "/vi-mo/chi-so/", "Lợi suất, EFFR")),
      intro="Tin USD trong tuần, giờ Việt Nam, kèm dự báo và số trước.", kicker="Vĩ mô"),
    P("/vi-mo/loi-suat/", "vi-mo", "Đường cong lợi suất Mỹ", "Lợi suất trái phiếu Mỹ",
      "Lợi suất trái phiếu chính phủ Mỹ theo kỳ hạn: hôm nay, 1 tháng trước, đầu năm.",
      grid(card("loi-suat", full=True)) + ART["curve"] + related(("Chỉ số vĩ mô Mỹ", "/vi-mo/chi-so/", "Lợi suất thực, EFFR")),
      intro="Hôm nay so với 1 tháng trước và đầu năm.", kicker="Vĩ mô"),
    P("/vi-mo/chi-so/", "vi-mo", "Chỉ số vĩ mô Mỹ", "Chỉ số vĩ mô Mỹ",
      "Lợi suất danh nghĩa, lợi suất thực, lạm phát kỳ vọng và EFFR, kèm tác động thường gặp lên từng tài sản.",
      grid(card("macro", full=True)) + ART["macro"] + related(("Lợi suất Mỹ", "/vi-mo/loi-suat/", "Cả đường cong"),
                                                             ("Vàng", "/thi-truong/vang/", "Lợi suất thực và vàng")),
      intro="So với khoảng 1 tháng trước, kèm tác động thường gặp lên từng tài sản.", kicker="Vĩ mô"),
    P("/vi-mo/ton-kho-dau/", "vi-mo", "Tồn kho dầu Mỹ (EIA) tuần này", "Báo cáo tồn kho dầu EIA",
      "Dầu thô, xăng, dầu chưng cất và Cushing theo báo cáo EIA hằng tuần.",
      grid(card("eia", full=True)) + ART["eia"] + related(("Dầu WTI", "/thi-truong/dau/", "Mọi số liệu về dầu"),
                                                         ("Tin dầu", "/tin-tuc/dau/", "Tin mới nhất")),
      intro="Báo cáo EIA hằng tuần, thứ Tư khoảng 21:30 giờ VN.", kicker="Vĩ mô"),

    # ---- Tin tức
    news_page("/tin-tuc/", "Tin thị trường", "Tin tức", "Tin về Vàng, chứng khoán Mỹ, dầu, crypto, Fed. Chỉ hiện tiêu đề và link về bài gốc.", ""),
    news_page("/tin-tuc/vang/", "Tin vàng", "Tin vàng", "Tin mới nhất về vàng từ các trang tin tài chính.", "GC"),
    news_page("/tin-tuc/chung-khoan/", "Tin chứng khoán Mỹ", "Tin S&P 500 · Nasdaq", "Tin mới nhất về chứng khoán Mỹ.", "ES NQ"),
    news_page("/tin-tuc/dau/", "Tin dầu", "Tin dầu", "Tin mới nhất về dầu, OPEC, tồn kho.", "CL"),
    news_page("/tin-tuc/crypto/", "Tin crypto", "Tin crypto", "Tin mới nhất về Bitcoin, Ether và thị trường crypto.", "CRYPTO"),
    news_page("/tin-tuc/fed/", "Tin Fed và vĩ mô", "Tin Fed & vĩ mô", "Tin về Fed, lạm phát, việc làm, tăng trưởng.", "FED MACRO"),
    news_page("/tin-tuc/chinh-thuc/", "Tin từ nguồn chính thức", "Nguồn chính thức", "Thông cáo từ Federal Reserve, EIA, CFTC.", "official"),

    # ---- Học
    P("/hoc/", "hoc", "Học order flow", "Học order flow",
      "Bốn khái niệm cơ bản để đọc dòng tiền và vị thế: footprint, delta, volume profile, COT.",
      '<div class="learn-grid">' + "".join(
          f'<a class="lesson-tile" href="{u}"><b>{lesson_page(i)[0]}</b><span>{lesson_page(i)[1]}</span>{svg("chev")}</a>'
          for i, u in enumerate(["/hoc/footprint/", "/hoc/delta-cvd/", "/hoc/volume-profile/", "/hoc/cot/"])) + "</div>",
      intro="Bốn khái niệm cơ bản để đọc dòng tiền và vị thế. Mỗi bài một trang.", kicker="Kiến thức nền", data=False),
    lesson("/hoc/footprint/", 0, [("Delta & CVD", "/hoc/delta-cvd/", "Bài tiếp theo"),
                                  ("Footprint trên Wyckdelta Chart", "/wyckdelta-chart/", "Xem ảnh thật")]),
    lesson("/hoc/delta-cvd/", 1, [("Volume Profile", "/hoc/volume-profile/", "Bài tiếp theo"),
                                  ("Footprint", "/hoc/footprint/", "Bài trước")]),
    lesson("/hoc/volume-profile/", 2, [("Báo cáo COT", "/hoc/cot/", "Bài tiếp theo"),
                                       ("Delta & CVD", "/hoc/delta-cvd/", "Bài trước")]),
    lesson("/hoc/cot/", 3, [("Quỹ lớn (COT)", "/vi-the/cot/", "Số liệu tuần này"),
                            ("Ai đang đông người", "/vi-the/dong-nguoi/", "COT Index 6 mã")]),

    # ---- Wyckdelta Chart
    P("/wyckdelta-chart/", "wyckdelta-chart", "Wyckdelta Chart · Order flow + GEX trên một biểu đồ",
      "Xem ai đang giữ giá, ngay trên chart",
      "Footprint, heatmap sổ lệnh, iceberg và các mức GEX trên một biểu đồ cho Vàng, ES, NQ, crypto.",
      read("features.html"),
      intro="Mọi ảnh dưới đây chụp từ Wyckdelta Chart với dữ liệu Vàng thật, phiên Mỹ ngày 11/11.",
      kicker="Tính năng", data=False, note=True),
]


# ------------------------------------------------------------------ page shell
def page(p, v_css, v_js):
    path, cat = p["path"], p["cat"]
    url = BASE + path
    title_tag = p["title"] if "Wyckdelta" in p["title"] else f'{p["title"]} · Wyckdelta'
    body_attrs = f' data-cat="{cat}"'
    if p["fold"]:
        body_attrs += ' data-fold="1"'
    if p["assets"]:
        body_attrs += f' data-assets="{p["assets"]}"'
    if p["news"]:
        body_attrs += f' data-news="{p["news"]}"'
    tabs = "".join(f'<a href="{SECTION[k][1]}"{" aria-current=\"true\"" if k == cat else ""}>{svg(i)}{l}</a>' for k, l, i in TABBAR)
    head_title = p["h1"]
    crumb = crumbs(cat, path, head_title)
    pill = '<span class="pill" id="updated">Đang tải dữ liệu…</span>' if p["data"] else ""
    intro = f'<p>{p["intro"]}</p>' if p["intro"] else ""
    kicker = f'<span class="kicker">{p["kicker"]}</span>' if p["kicker"] else ""
    h = "h2" if p["hero"] else "h1"
    parts = [
        f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title_tag}</title>
<meta name="description" content="{p["desc"]}">
<meta name="theme-color" content="#0b0f17">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Wyckdelta">
<meta property="og:title" content="{title_tag}">
<meta property="og:description" content="{p["desc"]}">
<meta property="og:image" content="{BASE}/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="manifest" href="/manifest.webmanifest">
<script src="/i18n.js?v=2"></script>
<script>try {{ if (localStorage.getItem("gt-theme") === "light") document.documentElement.dataset.theme = "light"; }} catch (e) {{}}</script>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/img/favicon-16.svg" type="image/svg+xml">
<link rel="icon" href="/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/img/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/app.css?v={v_css}">
</head>
<body{body_attrs}>
<!-- generated by scripts/build_pages.py: edit scripts/site_src/ or that script, not this file -->
<header class="topbar" id="top">
  <button class="iconbtn ghost" id="menu" type="button" aria-label="Menu" aria-controls="side" aria-expanded="false" title="Menu">
    {svg("menu")}
  </button>
  <a class="logo" href="/" aria-label="Wyckdelta, trang chủ"><img src="/img/logo.png" alt="" width="30" height="30">Wyckdelta</a>
  <form class="gsearch" id="gsearch" role="search" action="/tin-tuc/" method="get">
    <input id="gq" name="q" type="search" placeholder="Tìm tin thị trường… (Powell, CPI, OPEC, bitcoin)" autocomplete="off" aria-label="Tìm tin thị trường">
    <button type="submit" aria-label="Tìm">{svg("search")}</button>
  </form>
  <div class="tools">
    <div class="langsw" data-lang-switch role="group" aria-label="Ngôn ngữ / Language"><button type="button" data-l="VI">VI</button><button type="button" data-l="EN">EN</button></div>
    <button class="iconbtn" id="theme" type="button" aria-label="Đổi giao diện sáng / tối" title="Đổi giao diện sáng / tối">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18" fill="currentColor"/></svg>
    </button>
    <a class="btn sm chart-link" href="/chart.html"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19V5M4 19h16M8 15l3-4 3 2 5-6"/></svg>Mở Wyckdelta Chart</a>
    <a class="btn gold sm" href="{INBOX}" target="_blank" rel="noopener"><span class="cta-long">Inbox để nhận link dùng thử</span><span class="cta-short">Nhận link</span></a>
  </div>
</header>

<aside class="side" id="side" aria-label="Điều hướng">
  <nav class="rail">
    {rail(cat)}
  </nav>
  <div class="side-foot">
    <div class="langsw side-lang" data-lang-switch role="group" aria-label="Ngôn ngữ / Language"><button type="button" data-l="VI">VI</button><button type="button" data-l="EN">EN</button></div>
    <a class="btn gold" href="{INBOX}" target="_blank" rel="noopener">Inbox để nhận link dùng thử</a>
    <p>Công cụ phân tích dữ liệu, không phải lời khuyên đầu tư.</p>
  </div>
</aside>
<div class="scrim" id="scrim" hidden></div>
<nav class="tabbar" aria-label="Mục chính">
  {tabs}
  <button type="button" id="tab-more" aria-controls="side">{svg("menu")}Menu</button>
</nav>

<div class="shell">''']
    if p["note"]:
        parts.append('''<div class="site-note" role="note">
  <div class="wrap">
    <p>wyckdelta.com là trang giới thiệu và hướng dẫn. Biểu đồ nằm trong <b>Wyckdelta Chart</b>: app Windows, điện thoại và Mac.</p>
    <div class="sn-cases">
      <div class="sn-case"><span>Đã có tài khoản</span><a class="pri" href="/chart.html">Mở Wyckdelta Chart</a></div>
      <div class="sn-case"><span>Chưa có tài khoản</span><a href="/huong-dan.html">Cài đặt 3 bước</a></div>
      <div class="sn-case"><span>Tài khoản hết hạn</span><a href="https://t.me/wyckdeltachart" target="_blank" rel="noopener">Inbox Wyckdelta</a></div>
    </div>
  </div>
</div>''')
    if cat != "home":
        parts.append(subnav(cat, path))
    if p["ticker"]:
        parts.append('''<div class="wrap ticker-wrap">
  <div class="ticker" id="ticker" data-i18n-skip translate="no"></div>
  <a class="ticker-src" href="https://www.tradingview.com/" target="_blank" rel="noopener nofollow">Giá vàng giao ngay và chỉ số: TradingView, trễ theo quy định của sàn</a>
</div>''')
    if p["pulse"]:
        parts.append('<div class="wrap pulse-wrap"><div class="pulse" id="pulse"></div></div>')
    if p["hero"]:
        parts.append(read("hero.html").rstrip().replace('src="img/', 'src="/img/').replace('href="#thi-truong"', 'href="#nhip"'))
    parts.append(f'''<main class="wrap" id="nhip">
  {crumb}
  <div class="page-head">
    <div>
      {kicker}
      <{h}>{head_title}</{h}>
      {intro}
    </div>
    {pill}
  </div>
{p["body"]}''')
    if p["final"]:
        parts.append(read("final.html").rstrip().replace('src="img/', 'src="/img/').replace('href="huong-dan.html"', 'href="/huong-dan.html"'))
    parts.append("</main>\n")
    parts.append(read("footer.html").rstrip().replace('src="img/', 'src="/img/').replace('href="#top"', 'href="/"'))
    parts.append(f'''</div>

<script type="module" src="/app.js?v={v_js}"></script>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "5df5afcbbd9046bf8af0256168f49f57"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
''')
    html = "\n".join(x for x in parts if x)
    # features.html carries relative image paths
    html = html.replace('src="img/', 'src="/img/')
    return html


def out_path(path):
    return SITE / (path.strip("/") + "/index.html" if path != "/" else "index.html")


def build():
    v_css, v_js = ver("app.css"), ver("app.js", "charts.js")
    return {out_path(p["path"]): page(p, v_css, v_js) for p in PAGES}


def extras():
    """robots.txt and sitemap.xml for the section pages."""
    urls = [BASE + p["path"] for p in PAGES] + [BASE + "/huong-dan.html"]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    return {SITE / "sitemap.xml": sm, SITE / "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n"}


def main():
    pages = {**build(), **extras()}
    check = "--check" in sys.argv
    bad = []
    for f, html in pages.items():
        old = f.read_text(encoding="utf-8").replace("\r\n", "\n") if f.exists() else None
        if old == html:
            continue
        if check:
            bad.append(f.relative_to(ROOT))
        else:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(html, encoding="utf-8", newline="\n")
    if check and bad:
        print("out of date (run py -B scripts/build_pages.py):", *bad, sep="\n  ")
        sys.exit(1)
    print(f"{len(pages)} pages" + (" up to date" if check else " written"))


if __name__ == "__main__":
    main()
