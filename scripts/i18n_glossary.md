# Wyckdelta VI -> EN glossary (site translation)

Fixed choices (use exactly):
- Wyckdelta: unchanged (brand). Never add any other company or platform name that is not already in the Vietnamese.
- "Inbox để nhận link dùng thử" -> "Message us for a trial link"; "Nhận link" -> "Get link"
- "Nhịp thị trường (hôm nay)" -> "Market pulse (today)"
- "Quỹ lớn" -> "Large funds"; "quỹ đầu cơ" -> "hedge funds" (Managed Money); "nhà sản xuất và thương nhân" -> "producers and merchants"; "ngân hàng" (Swap Dealer) -> "banks (swap dealers)"
- "vị thế ròng" -> "net position"; "hợp đồng ròng" -> "net contracts"; "mua ròng / bán ròng" -> "net buying / net selling" (or net long / net short for positions)
- "COT Index", "COT", "Non-commercial", "Commercial", "Managed Money", "Legacy", "Disaggregated", "EIA", "CFTC", "GLD", "SPR", "TIPS", "EFFR", "FOMC", "CPI", "PCE", "NFP", "PMI", "GEX", "POC", "VAH", "VAL", "Value Area", "CVD", "delta", "footprint", "heatmap", "iceberg", "Call Wall", "Put Wall", "Gamma Flip", "SuperDOM", "TPO", "VWAP": keep as is.
- "đông người" (crowded positioning) -> "crowded"; "Bán đã đông / Mua đã đông" -> "Crowded short / Crowded long"
- "Áp lực" (bias tag) -> "Headwind"; "Hỗ trợ" -> "Tailwind"; "Trung tính" -> "Neutral"
- "thường hỗ trợ / thường gây áp lực" -> "usually supportive / usually a headwind"
- "Tin đỏ" (high-impact news) -> "High-impact news"; "tin cam" -> "medium-impact news"; "Đỏ" / "Cam" (chips) -> "High" / "Medium"
- "Lịch tin (tuần)" -> "(Weekly) economic calendar"; "Giờ VN" -> "Vietnam time"; "Dự báo" -> "Forecast"; "Trước" (previous value) -> "Previous"
- "Tồn kho dầu thô" -> "Crude oil inventories"; "triệu thùng" -> "million barrels"; "tr thùng" -> "M bbl"; "tấn" -> "tonnes"
- "Lợi suất thực" -> "Real yield"; "Đường cong lợi suất" -> "Yield curve"; "Vĩ mô" -> "Macro"
- "Sợ hãi tột độ / Sợ hãi / Trung lập / Tham lam / Tham lam tột độ" -> "Extreme Fear / Fear / Neutral / Greed / Extreme Greed"
- "Kịch bản" -> "Scenarios"; "Cách đọc và nguồn" -> "How to read · sources"
- "Vàng" -> "Gold"; "Dầu WTI" -> "WTI crude"; "S&P 500", "Nasdaq 100" unchanged
- Weekday / date words in fragments: "T2..T6" -> "Mon..Fri", "Hôm nay" -> "Today", "Ngày mai" -> "Tomorrow", "Hôm kia" -> "2 days ago", "vừa xong" -> "just now"
- Disclaimers: "không phải lời khuyên đầu tư" -> "not investment advice"; keep the full legal meaning, do not soften.

Rules:
- Many keys are FRAGMENTS of longer sentences built in code (text between numbers, links or bold tags). Translate the
  fragment so it still reads naturally when glued back in the same place; keep leading/trailing punctuation such as
  " · ", "(", ")", ":", "+", "%" exactly where they are; never add or drop numbers.
- Plain, short English a trader understands; US spelling; sentence case for headings.
- Output: ONE JSON object {"<vietnamese key exactly as given>": "<english>"} with every key, nothing else.

## Whole-block units (scripts/i18n_units_en.json)
- A unit key is a whole sentence / block. Markers like {0}…{/0} wrap inline elements (bold words, links, key
  names); {3/} is a line break, image or icon. Keep EVERY marker exactly once, with the same number, and put each
  pair around the English words that correspond to the Vietnamese words inside it (order may change). Do not add,
  drop or renumber markers. Text inside a marker pair that is a real on-screen label of another app (Tailscale,
  Windows, iPhone, Android, Chrome, Safari) must be the label as that app shows it IN ENGLISH.
- Real English UI labels to use: Windows SmartScreen "More info" then "Run anyway"; app stores "Install" / "Get" /
  "Open"; iPhone Share sheet "Add to Home Screen" then "Add"; Tailscale "Log in", "Connected", accept-invite button
  "Accept invite"; Chrome menu "Install app" / "Add to Home screen".
- Our own site / app: "Sign in" / "Sign out" (not Log in) except where it names Tailscale's own button.
- Dates: write "Nov 20, 2026" style for fixed dates in prose.
- Yield curve: "dốc lên" = "upward-sloping", "đảo ngược" = "inverted". Impact level "Trung bình" = "Medium".
- Units: "điểm %" = "pp"; one item vs many: use the right plural.
