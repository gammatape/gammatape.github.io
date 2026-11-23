"""Lấy tin từ các nguồn RSS miễn phí + lịch kinh tế, ghi ra site/data/news.json và calendar.json.

Chỉ dùng thư viện chuẩn của Python, chạy được trên GitHub Actions không cần cài gì.
Chỉ lưu tiêu đề, tóm tắt ngắn và link về bài gốc (không chép nguyên bài).
"""
import html
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

from common import ROOT, fetch, write_json

CONFIG = json.loads((ROOT / "feeds.json").read_text(encoding="utf-8"))

MAX_AGE = timedelta(hours=72)
MAX_AGE_OFFICIAL = timedelta(days=21)  # thông cáo Fed/EIA/CFTC ra thưa nên giữ lâu hơn
MAX_ITEMS = 400
SUMMARY_LEN = 220

# Nhãn -> từ khoá, so khớp nguyên từ, không phân biệt hoa thường, trên tiêu đề + tóm tắt
TOPICS = {
    "GC": ["gold", "xau", "bullion", "precious metals?", "silver",
           # "vàng" đứng một mình dễ dính "vững vàng", "đất vàng" nên dùng cụm cụ thể
           "giá vàng", "vàng miếng", "vàng nhẫn", "vàng sjc", "vàng thế giới", "vàng trong nước",
           "mua vàng", "bán vàng", "dự trữ vàng", "quỹ vàng", "thị trường vàng", "giá bạc"],
    # "stocks"/"equities" đứng một mình khớp cả chứng khoán Ả Rập, châu Âu, Trung Quốc: chỉ lấy cụm chỉ thị trường Mỹ
    "ES": ["s&p", "s&p 500", "spx", "dow jones", "the dow", "wall street", "u\\.?s\\.? stocks?", "american stocks?",
           "u\\.?s\\.? equities", "chứng khoán mỹ", "phố wall"],
    "NQ": ["nasdaq", "nq", "tech stocks", "megacap", "nvidia", "apple", "microsoft", "semiconductors?", "chips?"],
    "CL": ["oil", "crude", "opec", "brent", "wti", "gasoline", "petroleum", "eia", "giá dầu", "xăng dầu"],
    "CRYPTO": ["bitcoin", "btc", "ether", "ethereum", "solana", "crypto", "cryptocurrenc(?:y|ies)", "stablecoins?",
               "spot etfs?", "tiền số", "tiền mã hoá", "tiền mã hóa", "tiền điện tử", "tài sản số"],
    "FED": ["fed", "federal reserve", "fomc", "powell", "rate cuts?", "rate hikes?", "interest rates?",
            "monetary policy", "lãi suất"],
    "MACRO": ["cpi", "pce", "inflation", "jobs report", "payrolls?", "nfp", "gdp", "pmi", "unemployment",
              "retail sales", "treasury yields?", "tariffs?", "lạm phát", "việc làm", "tăng trưởng"],
}
TOPIC_RE = {t: re.compile(r"(?<!\w)(?:" + "|".join(words) + r")(?!\w)", re.IGNORECASE)
            for t, words in TOPICS.items()}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(text):
    text = html.unescape(TAG_RE.sub(" ", text or ""))
    return WS_RE.sub(" ", text).strip()


def shorten(text, n=SUMMARY_LEN):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"


def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def child_text(el, *names):
    for c in el:
        if local(c.tag) in names and (c.text or "").strip():
            return c.text
    return ""


def parse_feed(feed):
    root = ET.fromstring(fetch(feed["url"], timeout=20))
    items = []
    for el in root.iter():
        kind = local(el.tag)
        if kind not in ("item", "entry"):
            continue
        title = clean(child_text(el, "title"))
        if kind == "entry":  # Atom: link nằm trong thuộc tính href
            link = next((c.get("href") for c in el if local(c.tag) == "link" and c.get("href")), "")
        else:
            link = child_text(el, "link").strip()
        summary = clean(child_text(el, "description", "summary", "content"))
        date = parse_date(child_text(el, "pubDate", "published", "updated", "date"))
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "summary": shorten(summary) if summary != title else "",
            "source": feed["name"],
            "lang": feed.get("lang", "en"),
            "official": bool(feed.get("official")),
            "time": date.isoformat() if date else None,
        })
    return items


def tag_topics(item):
    text = f"{item['title']} {item['summary']}"
    tags = [t for t, rx in TOPIC_RE.items() if rx.search(text)]
    if item["source"].startswith("EIA") and "CL" not in tags:
        tags.append("CL")
    if item["source"].startswith("Fed") and "FED" not in tags:
        tags.append("FED")
    return tags


def norm_title(t):
    return re.sub(r"[^\w]", "", t.lower())[:80]


def get_news():
    feeds = CONFIG["feeds"]
    status = []

    def run(feed):
        try:
            return feed, parse_feed(feed), None
        except Exception as e:  # một nguồn lỗi không làm hỏng cả trang
            return feed, [], f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(run, feeds))

    now = datetime.now(timezone.utc)
    seen, news = set(), []
    for feed, items, err in results:
        status.append({"source": feed["name"], "ok": err is None, "count": len(items), "error": err})
        max_age = MAX_AGE_OFFICIAL if feed.get("official") else MAX_AGE
        for it in items:
            key = norm_title(it["title"])
            if key in seen:
                continue
            if it["time"] and now - datetime.fromisoformat(it["time"]) > max_age:
                continue
            seen.add(key)
            it["topics"] = tag_topics(it)
            news.append(it)

    news.sort(key=lambda x: x["time"] or "", reverse=True)
    return news[:MAX_ITEMS], status


# Lịch tin USD dựng từ lịch công bố chính thức của các cơ quan Mỹ (BLS, BEA, Census, Bộ Lao động, Fed, ISM, ĐH Michigan,
# EIA), giờ New York, nguồn từng loại ghi trong file. Không dùng feed lịch của Forex Factory: điều khoản cấm đăng lại.
# Dự báo / số trước của mọi đồng tiền: widget lịch kinh tế TradingView trên trang /vi-mo/lich-tin/.
US_CAL = ROOT / "scripts" / "us_release_calendar.json"
VN_TZ = timezone(timedelta(hours=7))
TITLES = {  # tên tiếng Anh theo cách app.js dịch (VI_EVENTS)
    "nfp": "Non-Farm Payrolls", "cpi": "CPI", "ppi": "PPI", "jolts": "JOLTS Job Openings", "eci": "Employment Cost Index",
    "pce": "PCE Price Index", "retail": "Retail Sales", "claims": "Unemployment Claims", "fomc": "FOMC Statement",
    "fomc_pc": "FOMC Press Conference", "fomc_min": "FOMC Meeting Minutes", "ism_mfg": "ISM Manufacturing PMI",
    "ism_svc": "ISM Services PMI", "eia": "Crude Oil Inventories",
}
STAGES = {  # loại tin có nhiều lần công bố cho cùng một kỳ: lấy lần nào từ tên trong file
    "gdp": [("advance", "Advance GDP"), ("second", "Prelim GDP"), ("third", "Final GDP")],
    "umich": [("prelim", "Prelim UoM Consumer Sentiment"), ("final", "Revised UoM Consumer Sentiment")],
}


def new_york(day, hhmm):
    """Giờ New York -> datetime có offset. Giờ mùa hè Mỹ: Chủ nhật thứ hai tháng 3 tới Chủ nhật đầu tháng 11 (tin
    công bố 08:30-14:30 nên mốc 02:00 của ngày đổi giờ không ảnh hưởng)."""
    d = date.fromisoformat(day)
    mar, nov = date(d.year, 3, 1), date(d.year, 11, 1)
    dst_start = mar + timedelta(days=(6 - mar.weekday()) % 7 + 7)
    dst_end = nov + timedelta(days=(6 - nov.weekday()) % 7)
    h, m = map(int, hhmm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=timezone(timedelta(hours=-4 if dst_start <= d < dst_end else -5)))


def week_window(now):
    """Tuần đang xem, tính theo giờ VN: thứ Hai 00:00 tới thứ Hai sau. Thứ Bảy, Chủ nhật thì xem tuần tới."""
    vn = now.astimezone(VN_TZ)
    monday = (vn - timedelta(days=vn.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if vn.weekday() >= 5:
        monday += timedelta(days=7)
    return monday, monday + timedelta(days=7)


def release_title(ev):
    key, name = ev["key"], ev.get("title", "")
    if key in STAGES:
        low = name.lower()
        return next((t for word, t in STAGES[key] if word in low), None)
    return TITLES.get(key)


def get_calendar(now=None):
    """(events, error, meta) của tuần đang xem, cùng định dạng app.js đã đọc (title, country, time, impact...)."""
    now = now or datetime.now(timezone.utc)
    try:
        raw = json.loads(US_CAL.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"{US_CAL.name}: {type(e).__name__}: {e}", {}
    start, end = week_window(now)
    events, last = [], None
    # Một dòng hỏng trong file (sửa tay) chỉ làm lịch báo lỗi, không được làm cả lần chạy (tin, thị trường) dừng
    try:
        for ev in raw["events"]:
            title = release_title(ev)
            if not title:
                return None, f"{US_CAL.name}: không đặt được tên cho {ev}", {}
            if ev.get("impact") not in ("High", "Medium"):   # app.js chỉ lọc / vẽ hai mức này
                return None, f"{US_CAL.name}: impact phải là High / Medium: {ev}", {}
            t = new_york(ev["date"], ev["time"])
            last = max(last, t) if last else t
            if start <= t < end:
                period = re.search(r"\(([^)]+)\)", ev.get("title", ""))
                events.append({"title": title, "country": "USD", "time": t.isoformat(), "impact": ev["impact"],
                               "forecast": "", "previous": "", "period": period.group(1) if period else "",
                               "verified": bool(ev.get("verified"))})
    except (KeyError, TypeError, ValueError) as e:
        return None, f"{US_CAL.name}: {type(e).__name__}: {e}", {}
    events.sort(key=lambda e: e["time"])
    meta = {"week_start": start.isoformat(), "source": "official", "covers_until": last.date().isoformat() if last else None}
    if last is None or last < start:
        return None, f"{US_CAL.name} hết dữ liệu (tới {meta['covers_until']}): cần thêm lịch công bố mới", meta
    return events, None, meta


def main():
    updated = datetime.now(timezone.utc).isoformat()
    news, status = get_news()
    events, cal_err, cal_meta = get_calendar()

    write_json("news.json", {"updated": updated, "items": news, "sources": status})
    # Lịch là file trong repo: lỗi (file hỏng, hết dữ liệu) thì ghi rõ lỗi, không giữ bản cũ của tuần khác
    cal = {"updated": updated, "events": events or [], "error": cal_err, **cal_meta}
    write_json("calendar.json", cal)

    ok = sum(s["ok"] for s in status)
    print(f"Tin: {len(news)} bài từ {ok}/{len(status)} nguồn. Lịch: {len(cal['events'])} sự kiện.")
    # "::warning::" hiện thành cảnh báo vàng trên trang lần chạy của GitHub Actions, không chỉ nằm trong log
    until = cal_meta.get("covers_until")
    if cal_err:
        print(f"::warning::Lịch tin USD lỗi: {cal_err}")
    elif until and date.fromisoformat(until) - date.today() < timedelta(days=60):
        print(f"::warning::{US_CAL.name} chỉ có lịch tới {until}: thêm lịch công bố mới của các cơ quan Mỹ")
    for s in status:
        if not s["ok"]:
            print(f"  ! {s['source']}: {s['error']}")
    if not news:
        sys.exit("Không lấy được tin nào.")


if __name__ == "__main__":
    main()
