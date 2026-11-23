# Wyckdelta

Địa chỉ: https://wyckdelta.com (GitHub Pages, repo `gammatape/gammatape.github.io`; địa chỉ cũ gammatape.github.io tự chuyển hướng về đây). DNS ở Cloudflare (DNS only), tên miền đã xác minh trong tổ chức gammatape.

Trang web của Wyckdelta: giới thiệu app (order flow + GEX trên một biểu đồ, ảnh chụp app thật, nút inbox nhận link dùng thử) và mục **Nhịp thị trường hôm nay** miễn phí cho mọi người: vĩ mô · vị thế · tin tức cho GC, ES, NQ, CL. Chạy với chi phí 0 đồng.

Bộ nhận diện giống bộ ảnh quảng cáo: nền #0b0f17, xanh #22c55e, vàng #f5b301, font Be Vietnam Pro. Giao diện tối là mặc định, có nút đổi sang sáng.

| Mục | Nguồn (miễn phí, không cần API key) | Tần suất |
|---|---|---|
| Ô nhịp thị trường (tin đỏ kế tiếp, lợi suất thực, COT Vàng, tồn kho dầu) | Tính trên trang từ dữ liệu bên dưới | Mỗi lần tải |
| Quỹ lớn đang nghiêng về đâu (4 mã, COT) | CFTC, báo cáo Legacy | Thứ Sáu hằng tuần |
| Ai đang mua, ai đang bán (quỹ đầu cơ / nhà sản xuất / ngân hàng, Vàng và Dầu) | CFTC, báo cáo Disaggregated | Thứ Sáu hằng tuần |
| Đường cong lợi suất Mỹ (hôm nay, 1 tháng trước, đầu năm) | U.S. Treasury, Daily Par Yield Curve | Hằng ngày |
| Tồn kho dầu Mỹ | EIA, Weekly Petroleum Status | Thứ Tư hằng tuần |
| Quỹ vàng SPDR (GLD): số tấn đang giữ, mua / bán mỗi phiên | File lưu trữ của SPDR Gold Shares (xlsx), chỉ đăng số tấn và thay đổi | Mỗi ngày giao dịch (tải 1 lần khi quỹ đã công bố, buổi sáng giờ VN; chưa có thì thử lại cách 3 giờ) |
| Động lực vĩ mô | U.S. Treasury (lợi suất danh nghĩa, lợi suất thực), Fed New York (EFFR) | Hằng ngày |
| Vàng trong nước so với thế giới (SJC miếng / nhẫn, thế giới quy đổi VNĐ / lượng, chênh lệch, tỷ lệ vàng / bạc) | Bảng giá công khai SJC (`PriceService.ashx`, robots.txt Allow: /), tỷ giá Vietcombank (API JSON công khai, robots.txt Allow: /), giá vàng / bạc gold-api.com (điều khoản cho dùng trên website) | 30 phút; lịch sử chênh lệch mỗi ngày một điểm, giữ 120 ngày |
| Chỉ số USD rộng (thay DXY) | Fed, bảng H.10 (dữ liệu công khai của Chính phủ Mỹ) | Hằng ngày |
| Lịch họp Fed (FOMC), giờ công bố theo giờ VN | federalreserve.gov/monetarypolicy/fomccalendars.htm | 30 phút |
| Cột phải: phiên Tokyo / London / New York, CME Globex mở / nghỉ | Tính trên trình duyệt theo múi giờ IANA (tự đổi giờ mùa hè / đông), chưa tính ngày lễ | Mỗi 30 giây |
| Kịch bản để quan sát | Tự suy ra từ COT, vĩ mô, EIA (mang tính giáo dục) | Mỗi lần cập nhật |
| Tin tức | RSS của Fed, EIA, CFTC và các trang tin tài chính | 30 phút |
| Lịch tin USD (giờ VN) | Lịch công bố chính thức của BLS, BEA, Census, Bộ Lao động Mỹ, Fed, ISM, ĐH Michigan, EIA, chép vào scripts/us_release_calendar.json (tới 31/12/2027; Actions báo cảnh báo khi còn dưới 60 ngày). Không dùng Forex Factory: điều khoản cấm đăng lại | Mỗi năm thêm lịch mới |
| Dự báo và số trước (mọi đồng tiền) | Widget lịch kinh tế TradingView trên /vi-mo/lich-tin/ | Trực tiếp |
| Tính năng Wyckdelta | Ảnh chụp app thật trong site/img (Vàng, phiên Mỹ 11/11) | — |
| Học order flow | Nội dung tĩnh | — |

Tin tức chỉ hiện tiêu đề, tóm tắt ngắn và link về bài gốc, không chép nguyên bài.

Quỹ GLD: điều khoản spdrgoldshares.com chỉ cho dùng cá nhân / phi thương mại, file lưu trữ ghi cấm phân phối lại khi
chưa có văn bản đồng ý, robots.txt của API chặn bot. Chủ chấp nhận rủi ro (2026-11-19) với điều kiện: tải một lần mỗi
ngày giao dịch, ghi nguồn + nhãn hiệu SPDR® + không liên kết, và gỡ ngay nếu quỹ yêu cầu (bỏ khối `#gld` và `get_gld`).

## Cấu trúc

```
feeds.json                    Danh sách nguồn RSS (sửa ở đây để thêm/bớt nguồn)
scripts/common.py             Hàm dùng chung
scripts/fetch_news.py         Tin tức + lịch kinh tế  -> site/data/news.json, calendar.json
scripts/fetch_market.py       COT, EIA, vĩ mô, quỹ GLD, kịch bản -> site/data/market.json
scripts/build_pages.py        Dựng mọi trang từ một khung: danh sách mục (NAV), danh sách trang (PAGES), bài chuyên sâu
scripts/site_src/             Phần HTML dùng chung: các thẻ dữ liệu (cards.html), hero, tính năng, bài học, lời kết, footer
site/index.html, site/<mục>/  Trang SINH RA bởi build_pages.py, không sửa tay (trang chủ, thi-truong/, vi-the/, vi-mo/, tin-tuc/, hoc/, wyckdelta-chart/)
site/app.css, site/app.js     CSS và mã chung của mọi trang (thẻ nào không có trên trang thì bỏ qua)
site/huong-dan.html           Hướng dẫn cài đặt + đăng nhập cho khách (iPhone / Android / Windows / Mac); ghi địa chỉ máy chủ wyckdelta.tail65e625.ts.net (chủ yêu cầu 2026-11-20; chỉ mở được qua Tailscale với link mời)
site/img/huong-dan/           Ảnh app Windows lấy từ Tuong-Chart apps/gammatape_viewer/tests/shots (Gmail mẫu); dang-nhap*, sau-dang-nhap, tai-khoan chụp từ ui_harness (tài khoản khách thử, không phải server thật)
site/charts.js                Bộ vẽ biểu đồ SVG tự viết (cột hai chiều, đường, đường cong, sparkline), không thư viện ngoài
site/CNAME                    Ghi tên miền riêng (wyckdelta.com). Trang đăng bằng Actions nên GitHub bỏ qua file này: tên miền đặt ở Settings → Pages
site/img/                     Ảnh chụp Wyckdelta (WebP, đã cắt bỏ thanh công cụ / danh sách theo dõi), logo, favicon, og.jpg 1200x630
.github/workflows/update.yml  Chạy 2 script mỗi 30 phút và đăng lên GitHub Pages
```

Các script chỉ dùng thư viện chuẩn Python, không cần cài gì thêm. Nguồn nào tạm lỗi thì giữ lại số liệu cũ, trang không bị trống.

### Các mục (2026-11-22)

Mỗi mục có URL riêng, kiểu cổng tài chính lớn: thanh rail trái (icon + tên mục), rê chuột / Tab vào mục thì hiện bảng
mục con; điện thoại là ngăn kéo (bấm mũi tên để mở mục con) + thanh tab dưới; mỗi trang có hàng tab mục con và
breadcrumb. Link cũ dạng `wyckdelta.com/#cot` tự chuyển sang trang mới (bảng `OLD` trong app.js).

| Mục | Trang con |
|---|---|
| Thị trường `/thi-truong/` | Vàng, S&P 500 · Nasdaq, Dầu WTI, Crypto (mỗi mã: COT riêng, kịch bản, vĩ mô tác động, "Điều cần theo dõi") |
| Vị thế `/vi-the/` | Quỹ lớn (COT), Ai mua ai bán, Ai đang đông người, Quỹ vàng GLD |
| Vĩ mô `/vi-mo/` | Lịch tin tuần, Lợi suất Mỹ, Chỉ số vĩ mô Mỹ, Tồn kho dầu |
| Tin tức `/tin-tuc/` | Vàng, S&P · Nasdaq, Dầu, Crypto, Fed & vĩ mô, Nguồn chính thức |
| Học `/hoc/` | Footprint, Delta & CVD, Volume Profile, Báo cáo COT (mỗi bài một trang) |
| Wyckdelta Chart `/wyckdelta-chart/` | Tính năng, Cài đặt app (huong-dan.html), Mở Wyckdelta Chart (chart.html) |

Sửa nội dung hay thêm trang: sửa `scripts/build_pages.py` / `scripts/site_src/`, rồi

```bash
py -B scripts/build_pages.py
py -B scripts/i18n_build.py --strict
py -B scripts/build_pages.py --check
```

## Chạy thử trên máy

```bash
py scripts/fetch_news.py
```

```bash
py scripts/fetch_market.py
```

```bash
py -m http.server 8771 --bind 127.0.0.1 --directory site
```

Rồi mở http://127.0.0.1:8771

## Đăng lên mạng miễn phí (GitHub Pages) bằng GitHub Desktop

1. GitHub Desktop: **File → Add local repository…**, chọn thư mục này. Khi app báo chưa phải repository, bấm **create a repository** rồi **Create repository**.
2. Bấm **Publish repository**, **bỏ tích** "Keep this code private" (repo phải công khai thì mới miễn phí), rồi **Publish**.
3. Trên github.com, mở repo: **Settings → Pages → Source: GitHub Actions**.
4. Tab **Actions** → workflow "Cập nhật dữ liệu" → **Run workflow**. Chờ dấu ✅ xanh.
5. Địa chỉ web hiện ở **Settings → Pages**.

Sau này sửa file trên máy thì vào GitHub Desktop, ghi chú thay đổi, bấm **Commit to main** rồi **Push origin**. Trang tự đăng lại.

GitHub tự tắt lịch chạy định kỳ nếu repo không có commit nào trong 60 ngày. Khi đó vào tab Actions bấm bật lại.

## Miễn trừ trách nhiệm

Nội dung chỉ nhằm mục đích giáo dục và cung cấp thông tin, không phải lời khuyên đầu tư. Giao dịch hợp đồng tương lai có rủi ro cao và có thể mất toàn bộ vốn.
