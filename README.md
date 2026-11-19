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
| Quỹ vàng SPDR (GLD): số tấn đang giữ, mua / bán mỗi phiên | File lưu trữ của SPDR Gold Shares (xlsx), chỉ đăng số tấn và thay đổi | Mỗi ngày giao dịch (tải 1 lần, sau 6:00 giờ VN) |
| Động lực vĩ mô | U.S. Treasury (lợi suất danh nghĩa, lợi suất thực), Fed New York (EFFR) | Hằng ngày |
| Kịch bản để quan sát | Tự suy ra từ COT, vĩ mô, EIA (mang tính giáo dục) | Mỗi lần cập nhật |
| Tin tức | RSS của Fed, EIA, CFTC và các trang tin tài chính | 30 phút |
| Lịch vĩ mô (giờ VN) | Forex Factory | 30 phút |
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
site/index.html               Trang web (không cần build)
site/huong-dan.html           Hướng dẫn cài đặt cho khách (iPhone / Android / Windows / Mac), không ghi địa chỉ máy chủ
site/img/huong-dan/           Ảnh app Windows lấy từ Tuong-Chart apps/gammatape_viewer/tests/shots (Gmail mẫu)
site/charts.js                Bộ vẽ biểu đồ SVG tự viết (cột hai chiều, đường, đường cong, sparkline), không thư viện ngoài
site/CNAME                    Ghi tên miền riêng (wyckdelta.com). Trang đăng bằng Actions nên GitHub bỏ qua file này: tên miền đặt ở Settings → Pages
site/img/                     Ảnh chụp Wyckdelta (WebP, đã cắt bỏ thanh công cụ / danh sách theo dõi), logo, favicon, og.jpg 1200x630
.github/workflows/update.yml  Chạy 2 script mỗi 30 phút và đăng lên GitHub Pages
```

Các script chỉ dùng thư viện chuẩn Python, không cần cài gì thêm. Nguồn nào tạm lỗi thì giữ lại số liệu cũ, trang không bị trống.

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
