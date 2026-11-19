"""Lấy dữ liệu thị trường công khai, miễn phí, không cần API key, ghi ra site/data/market.json:

- COT (vị thế quỹ lớn) từ báo cáo Legacy của CFTC
- Vị thế theo nhóm (quỹ đầu cơ, nhà sản xuất, ngân hàng) cho Vàng và Dầu từ báo cáo Disaggregated của CFTC
- Tồn kho dầu hằng tuần từ EIA
- Lợi suất trái phiếu (danh nghĩa và thực) và đường cong lợi suất từ Bộ Tài chính Mỹ, lãi suất EFFR từ Fed New York
- Số tấn vàng quỹ SPDR Gold Shares (GLD) nắm giữ, từ file lưu trữ công khai của quỹ
- Kịch bản quan sát mang tính giáo dục, suy ra từ các số liệu trên
Tất cả là dữ liệu công khai của cơ quan nhà nước Mỹ.
"""
import csv
import functools
import io
import json
import zipfile
from datetime import date, datetime, timedelta, timezone

from common import fetch, previous_json, write_json

# ---------------------------------------------------------------- COT ----
ASSETS = {
    "GC": {"name": "Vàng", "code": "088691"},
    "ES": {"name": "S&P 500 E-mini", "code": "13874A"},
    "NQ": {"name": "Nasdaq 100 E-mini", "code": "209742"},
    "CL": {"name": "Dầu WTI", "code": "067651"},
    "BTC": {"name": "Bitcoin (CME)", "code": "133741"},
    "ETH": {"name": "Ether (CME)", "code": "146021"},
}
COT_URL = "https://www.cftc.gov/files/dea/history/deacot{year}.zip"


def cot_index(values, weeks):
    """Vị trí của giá trị mới nhất trong biên cao–thấp của N tuần gần nhất (0–100)."""
    window = values[-weeks:]
    lo, hi = min(window), max(window)
    return round(100 * (window[-1] - lo) / (hi - lo)) if hi > lo else 50


def get_cot(prev):
    # Báo cáo chốt số thứ Ba, công bố thứ Sáu. Bản cũ còn mới (chưa tới kỳ công bố sau) thì dùng lại.
    # Danh sách mã đổi (vd. thêm BTC, ETH) thì tải lại ngay.
    if prev and prev.get("cot") and set(prev["cot"].get("assets", {})) == set(ASSETS):
        last = date.fromisoformat(prev["cot"]["report_date"])
        if date.today() < last + timedelta(days=10):
            return prev["cot"], "giữ bản cũ (chưa có báo cáo mới)"

    rows = {k: [] for k in ASSETS}
    codes = {a["code"]: k for k, a in ASSETS.items()}
    this_year = date.today().year
    for year in (this_year - 3, this_year - 2, this_year - 1, this_year):
        try:
            z = zipfile.ZipFile(io.BytesIO(fetch(COT_URL.format(year=year), timeout=60)))
        except Exception:
            if year == this_year:
                raise
            continue
        text = z.read(z.namelist()[0]).decode("latin-1")
        for r in csv.DictReader(io.StringIO(text)):
            key = codes.get(r["CFTC Contract Market Code"].strip())
            if key:
                rows[key].append({
                    "d": r["As of Date in Form YYYY-MM-DD"].strip(),
                    "long": int(r["Noncommercial Positions-Long (All)"]),
                    "short": int(r["Noncommercial Positions-Short (All)"]),
                    "oi": int(r["Open Interest (All)"]),
                })

    out = {}
    for key, rs in rows.items():
        rs = sorted({r["d"]: r for r in rs}.values(), key=lambda r: r["d"])  # bỏ trùng, xếp theo ngày
        nets = [r["long"] - r["short"] for r in rs]
        cur, prev_w = rs[-1], rs[-2]
        out[key] = {
            "name": ASSETS[key]["name"],
            "net": nets[-1],
            "change": nets[-1] - nets[-2],
            "long": cur["long"], "short": cur["short"], "oi": cur["oi"],
            "long_change": cur["long"] - prev_w["long"], "short_change": cur["short"] - prev_w["short"],
            "net_pct_oi": round(100 * nets[-1] / cur["oi"], 1),
            "index26": cot_index(nets, 26),
            "index156": cot_index(nets, 156),
            "history": [{"d": r["d"], "net": n} for r, n in zip(rs[-52:], nets[-52:])],
        }
    report = max(a["history"][-1]["d"] for a in out.values())
    return {"report_date": report, "assets": out}, None


# ------------------------------------------ Vị thế theo nhóm (Disaggregated) ----
FLOW_ASSETS = ("GC", "CL")  # báo cáo Disaggregated chỉ có cho hàng hoá
DISAGG_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"


def get_flows(prev):
    """Quỹ đầu cơ (Managed Money), nhà sản xuất / thương nhân, ngân hàng (Swap Dealer): vị thế ròng 52 tuần."""
    if prev and prev.get("flows"):
        last = date.fromisoformat(prev["flows"]["report_date"])
        if date.today() < last + timedelta(days=10):
            return prev["flows"], "giữ bản cũ (chưa có báo cáo mới)"
    codes = {ASSETS[k]["code"]: k for k in FLOW_ASSETS}
    rows = {k: {} for k in FLOW_ASSETS}
    this_year = date.today().year
    for year in (this_year - 1, this_year):
        z = zipfile.ZipFile(io.BytesIO(fetch(DISAGG_URL.format(year=year), timeout=60)))
        for r in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("latin-1"))):
            key = codes.get(r["CFTC_Contract_Market_Code"].strip())
            if not key:
                continue
            n = lambda c: int(r[c].strip() or 0)
            rows[key][r["Report_Date_as_YYYY-MM-DD"].strip()] = {
                "mm": n("M_Money_Positions_Long_All") - n("M_Money_Positions_Short_All"),
                "mm_long": n("M_Money_Positions_Long_All"), "mm_short": n("M_Money_Positions_Short_All"),
                "prod": n("Prod_Merc_Positions_Long_All") - n("Prod_Merc_Positions_Short_All"),
                "swap": n("Swap_Positions_Long_All") - n("Swap__Positions_Short_All"),
            }
    out = {}
    for key, by_date in rows.items():
        ds = sorted(by_date)[-53:]
        if len(ds) < 2:
            raise ValueError(f"Thiếu dữ liệu Disaggregated cho {key}")
        cur, old = by_date[ds[-1]], by_date[ds[-2]]
        out[key] = {
            "mm": cur["mm"], "mm_change": cur["mm"] - old["mm"], "mm_long": cur["mm_long"], "mm_short": cur["mm_short"],
            "prod": cur["prod"], "prod_change": cur["prod"] - old["prod"],
            "swap": cur["swap"], "swap_change": cur["swap"] - old["swap"],
            "history": [{"d": d, "mm": by_date[d]["mm"], "prod": by_date[d]["prod"], "swap": by_date[d]["swap"]} for d in ds[-52:]],
        }
    return {"report_date": max(a["history"][-1]["d"] for a in out.values()), "assets": out}, None


# ---------------------------------------------------------------- EIA ----
EIA_URL = "https://ir.eia.gov/wpsr/table1.csv"
EIA_ROWS = [  # (nhãn hiển thị, đầu dòng trong file EIA)
    ("Dầu thô thương mại (không gồm SPR)", "Commercial (Excluding SPR)"),
    ("Kho dự trữ chiến lược (SPR)", "Strategic Petroleum Reserve"),
    ("Xăng", "Total Motor Gasoline"),
    ("Dầu chưng cất (diesel, dầu sưởi)", "Distillate Fuel Oil"),
]


def num(s):
    return float(s.replace(",", "").strip() or 0)


def get_eia():
    text = fetch(EIA_URL).decode("latin-1").replace("\x1a", "")
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]  # "STUB_1", tuần này, tuần trước, chênh lệch, %, cùng kỳ năm trước, ...
    week = datetime.strptime(head[1], "%m/%d/%y").date().isoformat()
    out = []
    for label, stub in EIA_ROWS:
        r = next((r for r in rows if r and r[0].strip().startswith(stub)), None)
        if not r:
            continue
        cur, prev = num(r[1]), num(r[2])
        out.append({"name": label, "value": cur, "change": round(cur - prev, 3),
                    "year_ago": num(r[5]), "unit": "triệu thùng"})
    if not out:
        raise ValueError("Không đọc được bảng EIA")
    return {"week": week, "rows": out}


# -------------------------------------------------------------- Vĩ mô ----
TREASURY = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
            "{year}/all?type={kind}&field_tdr_date_value={year}&page&_format=csv")
EFFR_URL = "https://markets.newyorkfed.org/api/rates/unsecured/effr/last/30.json"


@functools.lru_cache(maxsize=None)
def treasury(kind):
    """Trả về danh sách (ngày, {kỳ hạn: lợi suất}) từ mới đến cũ: cả năm nay, thêm năm trước nếu năm nay chưa đủ 30 phiên."""
    series = []
    for year in (date.today().year, date.today().year - 1):
        text = fetch(TREASURY.format(year=year, kind=kind)).decode("utf-8-sig")
        for r in csv.DictReader(io.StringIO(text)):
            d = datetime.strptime(r.pop("Date"), "%m/%d/%Y").date()
            series.append((d, {k.strip().upper(): float(v) for k, v in r.items() if v}))
        if len(series) > 30:
            break
    return sorted(series, key=lambda x: x[0], reverse=True)


def month_ago(series):
    target = series[0][0] - timedelta(days=30)
    return next((s for s in series if s[0] <= target), series[-1])


# Quan hệ phổ biến khi chỉ số TĂNG: +1 = thường hỗ trợ giá, -1 = thường gây áp lực. Mang tính giáo dục.
IMPACT = {
    "real10": {"GC": -1, "ES": -1, "NQ": -1, "CL": 0, "BTC": -1, "ETH": -1},
    "y10":    {"GC": -1, "ES": -1, "NQ": -1, "CL": 0, "BTC": -1, "ETH": -1},
    "y2":     {"GC": -1, "ES": -1, "NQ": -1, "CL": 0, "BTC": -1, "ETH": -1},
    "be10":   {"GC": 1, "ES": 0, "NQ": 0, "CL": 1, "BTC": 0, "ETH": 0},
    "curve":  {"GC": 0, "ES": 0, "NQ": 0, "CL": 0, "BTC": 0, "ETH": 0},
    "effr":   {"GC": -1, "ES": -1, "NQ": -1, "CL": 0, "BTC": -1, "ETH": -1},
}
FLAT = 0.05  # thay đổi dưới 0,05 điểm % xem như đi ngang


SHORT = {"real10": "lợi suất thực", "y10": "lợi suất 10 năm", "y2": "lợi suất 2 năm",
         "be10": "lạm phát kỳ vọng", "curve": "chênh lệch 10–2 năm", "effr": "lãi suất EFFR"}


def macro_item(key, name, cur, old, unit, note, series=None):
    chg = round(cur[1] - old[1], 2)
    direction = 0 if abs(chg) < FLAT else (1 if chg > 0 else -1)
    return {
        "key": key, "name": name, "short": SHORT[key], "value": round(cur[1], 2), "date": cur[0].isoformat(),
        "prev": round(old[1], 2), "prev_date": old[0].isoformat(), "change": chg, "unit": unit,
        "impact": {a: s * direction for a, s in IMPACT[key].items()}, "note": note,
        # khoảng 1 tháng gần nhất, cũ -> mới, để vẽ đường xu hướng
        "history": [[d.isoformat(), round(v, 3)] for d, v in reversed(series or []) if d >= old[0]],
    }


def get_macro():
    nom, real = treasury("daily_treasury_yield_curve"), treasury("daily_treasury_real_yield_curve")
    pick = lambda series, col: [(d, v[col]) for d, v in series if col in v]
    y10, y2, r10 = pick(nom, "10 YR"), pick(nom, "2 YR"), pick(real, "10 YR")
    real_by_date = dict(r10)
    be = [(d, v - real_by_date[d]) for d, v in y10 if d in real_by_date]
    y2_by_date = dict(y2)
    curve = [(d, v - y2_by_date[d]) for d, v in y10 if d in y2_by_date]

    items = [
        macro_item("real10", "Lợi suất thực 10 năm (TIPS)", r10[0], month_ago(r10), "%",
                   "Chi phí cơ hội của việc giữ vàng. Tăng thường gây áp lực lên vàng và cổ phiếu công nghệ.", r10),
        macro_item("y10", "Lợi suất trái phiếu 10 năm", y10[0], month_ago(y10), "%",
                   "Mức chiết khấu cho định giá cổ phiếu. Tăng nhanh thường làm Nasdaq chịu áp lực hơn S&P.", y10),
        macro_item("y2", "Lợi suất 2 năm", y2[0], month_ago(y2), "%",
                   "Phản ánh kỳ vọng lãi suất Fed trong 1–2 năm tới.", y2),
        macro_item("be10", "Lạm phát kỳ vọng 10 năm (breakeven)", be[0], month_ago(be), "%",
                   "= lợi suất danh nghĩa − lợi suất thực. Tăng thường hỗ trợ vàng và dầu.", be),
        macro_item("curve", "Chênh lệch 10 năm − 2 năm", curve[0], month_ago(curve), "điểm %",
                   "Âm (đường cong đảo ngược) từng đi trước nhiều đợt suy thoái.", curve),
    ]
    try:
        effr = json.loads(fetch(EFFR_URL))["refRates"]
        s = [(date.fromisoformat(r["effectiveDate"]), r["percentRate"]) for r in effr]
        items.append(macro_item("effr", "Lãi suất qua đêm Fed (EFFR)", s[0], s[-1], "%",
                                f"Biên mục tiêu của Fed: {effr[0]['targetRateFrom']}–{effr[0]['targetRateTo']}%.", s))
    except Exception:
        pass
    return items


CURVE_COLS = [("1 MO", "1T"), ("3 MO", "3T"), ("6 MO", "6T"), ("1 YR", "1N"), ("2 YR", "2N"), ("3 YR", "3N"),
              ("5 YR", "5N"), ("7 YR", "7N"), ("10 YR", "10N"), ("20 YR", "20N"), ("30 YR", "30N")]


def get_curve():
    """Đường cong lợi suất danh nghĩa: phiên mới nhất, khoảng 1 tháng trước và phiên đầu tiên của năm."""
    nom = [(d, v) for d, v in treasury("daily_treasury_yield_curve") if all(c in v for c, _ in CURVE_COLS)]
    year_start = min((s for s in nom if s[0].year == nom[0][0].year), key=lambda s: s[0])
    pick = lambda name, s: {"name": name, "date": s[0].isoformat(), "v": [s[1][c] for c, _ in CURVE_COLS]}
    return {"labels": [l for _, l in CURVE_COLS],
            "series": [pick("Hôm nay", nom[0]), pick("1 tháng trước", month_ago(nom)), pick("Đầu năm", year_start)]}


# ----------------------------------------------------- Quỹ vàng GLD ----
# File lưu trữ chính thức của SPDR Gold Shares (xlsx), cột "Tonnes of Gold". Quỹ cập nhật mỗi ngày giao dịch sau giờ
# đóng cửa New York. Chỉ đăng số tấn và thay đổi (như báo chí vẫn đăng), không đăng lại cả file.
# Điều khoản của quỹ chỉ cho dùng cá nhân / phi thương mại và robots.txt của API chặn bot: chủ chấp nhận rủi ro
# (2026-11-19), nên tải ít nhất có thể (một lần mỗi ngày giao dịch), ghi nguồn + nhãn hiệu, quỹ yêu cầu thì gỡ ngay.
GLD_URL = "https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en"
GLD_SHEET = "US GLD Historical Archive"
GLD_KEEP_DAYS = 183  # khoảng 6 tháng cho biểu đồ
GLD_SLOT_HOUR = 23  # giờ UTC (6:00 VN): quỹ đã công bố số của phiên New York vừa đóng


def gld_slot(now):
    """Mốc tải gần nhất: 23:00 UTC của ngày giao dịch gần nhất (thứ 7, chủ nhật lùi về thứ 6)."""
    s = now.replace(hour=GLD_SLOT_HOUR, minute=0, second=0, microsecond=0)
    if now < s:
        s -= timedelta(days=1)
    while s.weekday() >= 5:
        s -= timedelta(days=1)
    return s


def xlsx_rows(blob, sheet_name):
    """Đọc một sheet xlsx bằng thư viện chuẩn: danh sách hàng, mỗi hàng là {cột: giá trị chuỗi}."""
    import re
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rid = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    z = zipfile.ZipFile(io.BytesIO(blob))
    strings = ["".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))
               for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    sheet = next(s for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", ns) if s.get("name") == sheet_name)
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = next(r.get("Target") for r in rels if r.get("Id") == sheet.get(rid)).lstrip("/")
    root = ET.fromstring(z.read(target if target.startswith("xl/") else "xl/" + target))
    rows = []
    for row in root.iter(f"{{{ns['m']}}}row"):
        out = {}
        for c in row.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is None:
                continue
            col = re.match(r"[A-Z]+", c.get("r")).group()
            out[col] = strings[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(out)
    return rows


def get_gld(prev):
    old = prev.get("gld")
    if old and datetime.fromisoformat(old["fetched"]) >= gld_slot(datetime.now(timezone.utc)):
        return old  # đã tải sau mốc của ngày giao dịch gần nhất: không gọi lại máy chủ của quỹ
    rows = xlsx_rows(fetch(GLD_URL, timeout=60), GLD_SHEET)
    head = rows[0]
    col = {name: c for c, name in head.items()}
    dcol, tcol = col["Date"], col["Tonnes of Gold"]
    series = []
    for r in rows[1:]:
        try:
            d = datetime.strptime(r[dcol].strip(), "%d-%b-%Y").date()
            t = float(r[tcol])
        except (KeyError, ValueError):
            continue  # ngày nghỉ ghi chữ "HOLIDAY", hoặc hàng trống
        series.append((d, t))
    series.sort(key=lambda x: x[0], reverse=True)  # mới -> cũ, như các chuỗi lợi suất
    if len(series) < 30:
        raise ValueError("File GLD quá ít dòng")
    cur = series[0]
    ago = lambda days: next((s for s in series if s[0] <= cur[0] - timedelta(days=days)), series[-1])
    year_end = next(s for s in series if s[0].year < cur[0].year)
    chg = lambda old: round(cur[1] - old[1], 2)
    last_year = [t for d, t in series if d > cur[0] - timedelta(days=365)]
    return {
        "fetched": datetime.now(timezone.utc).isoformat(), "date": cur[0].isoformat(), "tonnes": round(cur[1], 2),
        "d1": chg(series[1]), "d1_date": series[1][0].isoformat(),
        "w1": chg(ago(7)), "m1": chg(ago(30)), "ytd": chg(year_end), "year_end_date": year_end[0].isoformat(),
        "high52": round(max(last_year), 2), "low52": round(min(last_year), 2),
        "history": [[d.isoformat(), round(t, 2)] for d, t in reversed(series) if d > cur[0] - timedelta(days=GLD_KEEP_DAYS)],
    }


# ------------------------------------------------------------- Crypto ----
# Giá: CoinGecko (API công khai, phải ghi nguồn). Tâm lý: Crypto Fear & Greed Index của alternative.me (phải ghi nguồn).
COINS = [("bitcoin", "BTC", "Bitcoin"), ("ethereum", "ETH", "Ether"), ("solana", "SOL", "Solana")]
CG_URL = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids}"
          "&sparkline=true&price_change_percentage=24h,7d,30d")
FNG_URL = "https://api.alternative.me/fng/?limit=30"
FNG_VI = {"Extreme Fear": "Sợ hãi tột độ", "Fear": "Sợ hãi", "Neutral": "Trung lập",
          "Greed": "Tham lam", "Extreme Greed": "Tham lam tột độ"}


def get_crypto():
    rows = {r["id"]: r for r in json.loads(fetch(CG_URL.format(ids=",".join(c[0] for c in COINS))))}
    coins = []
    for cid, sym, name in COINS:
        r = rows[cid]
        spark = (r.get("sparkline_in_7d") or {}).get("price") or []
        step = max(1, len(spark) // 56)  # khoảng 56 điểm là đủ cho đường 7 ngày
        pts = spark[::step]
        if spark and pts[-1] != spark[-1]:
            pts.append(spark[-1])
        coins.append({
            "sym": sym, "name": name, "price": r["current_price"],
            "ch24": r.get("price_change_percentage_24h_in_currency"),
            "ch7": r.get("price_change_percentage_7d_in_currency"),
            "ch30": r.get("price_change_percentage_30d_in_currency"),
            "high24": r.get("high_24h"), "low24": r.get("low_24h"),
            "spark": [round(v, 2) for v in pts],
        })
    fng = None
    try:
        data = json.loads(fetch(FNG_URL))["data"]  # mới -> cũ
        fng = {"value": int(data[0]["value"]), "label": FNG_VI.get(data[0]["value_classification"], data[0]["value_classification"]),
               "history": [int(d["value"]) for d in reversed(data)]}
    except Exception as e:
        print(f"  ! fear & greed: {type(e).__name__}: {e}")
    return {"time": datetime.now(timezone.utc).isoformat(), "coins": coins, "fng": fng}


# ----------------------------------------------------------- Kịch bản ----
def scenarios(cot, macro, eia, gld=None):
    """Gợi ý những điều nên quan sát, suy ra theo quy tắc đơn giản. Không phải khuyến nghị."""
    out = {}
    for key in ASSETS:
        notes = []
        c = cot["assets"].get(key) if cot else None
        if c:
            i = c["index156"]
            if i >= 80:
                notes.append(f"Quỹ lớn đang mua ròng gần mức cao nhất 3 năm (COT Index {i}). "
                             "Vị thế đông người dễ bị chốt lời mạnh khi có tin bất lợi.")
            elif i <= 20:
                notes.append(f"Vị thế ròng của quỹ lớn gần mức thấp nhất 3 năm (COT Index {i}). "
                             "Bên bán đã đông, chú ý khả năng đảo chiều khi có tin tốt.")
            else:
                notes.append(f"Vị thế quỹ lớn ở vùng giữa (COT Index {i}), chưa cực đoan.")
            if c["change"]:
                way = "tăng" if c["change"] > 0 else "giảm"
                notes.append(f"Tuần qua vị thế ròng {way} {abs(c['change']):,} hợp đồng.".replace(",", "."))
        moved = lambda sign: [f"{m['short']} {'tăng' if m['change'] > 0 else 'giảm'}"
                              for m in macro if m["impact"].get(key) == sign]
        support, pressure = moved(1), moved(-1)
        score = len(support) - len(pressure)
        if support:
            notes.append("Vĩ mô 1 tháng qua hỗ trợ: " + ", ".join(support) + ".")
        if pressure:
            notes.append("Vĩ mô 1 tháng qua gây áp lực: " + ", ".join(pressure) + ".")
        if not support and not pressure:
            notes.append("Các chỉ số vĩ mô chính gần như đi ngang trong 1 tháng qua.")
        if key == "CL" and eia:
            crude = eia["rows"][0]
            way = "giảm" if crude["change"] < 0 else "tăng"
            notes.append(f"Tồn kho dầu thô thương mại tuần gần nhất {way} {abs(crude['change']):.1f} triệu thùng"
                         + (" (thường được đọc là cầu mạnh)." if crude["change"] < 0 else " (thường được đọc là cầu yếu)."))
        if key == "GC" and gld and abs(gld["m1"]) >= 0.5:
            way = "mua ròng" if gld["m1"] > 0 else "bán ròng"
            vn = lambda v: f"{v:,.1f}".replace(",", " ").replace(".", ",").replace(" ", ".")  # 1.044,4
            notes.append(f"Quỹ vàng SPDR (GLD) 1 tháng qua {way} {vn(abs(gld['m1']))} tấn, đang giữ {vn(gld['tonnes'])} tấn.")
        out[key] = {"bias": (score > 0) - (score < 0), "notes": notes}
    return out


def main():
    prev = previous_json("market.json") or {}
    data = {"updated": datetime.now(timezone.utc).isoformat(), "errors": {}}
    for name, fn in (("cot", lambda: get_cot(prev)), ("flows", lambda: get_flows(prev)), ("eia", get_eia),
                     ("macro", get_macro), ("curve", get_curve), ("crypto", get_crypto), ("gld", lambda: get_gld(prev))):
        try:
            res = fn()
            if name in ("cot", "flows"):
                res, info = res
                if info:
                    print(f"{name}: {info}")
            data[name] = res
        except Exception as e:
            data["errors"][name] = f"{type(e).__name__}: {e}"
            data[name] = prev.get(name)  # nguồn lỗi thì giữ bản cũ
            print(f"  ! {name}: {data['errors'][name]}")
    data["scenarios"] = scenarios(data.get("cot"), data.get("macro") or [], data.get("eia"), data.get("gld"))
    write_json("market.json", data)
    cot = data.get("cot") or {}
    print(f"COT {cot.get('report_date')}, nhóm {(data.get('flows') or {}).get('report_date')}, "
          f"EIA {(data.get('eia') or {}).get('week')}, vĩ mô {len(data.get('macro') or [])} chỉ số, "
          f"đường cong {((data.get('curve') or {}).get('series') or [{}])[0].get('date')}.")


if __name__ == "__main__":
    main()
