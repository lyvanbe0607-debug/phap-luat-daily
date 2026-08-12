# Pháp luật Daily

Tự động tổng hợp văn bản pháp luật mới từ Thư Viện Pháp Luật và gửi bản tin email mỗi ngày lúc **08:00 giờ Việt Nam**.

Nguồn chính: https://thuvienphapluat.vn/van-ban-moi

## Cách cài đặt

1. Upload toàn bộ các file trong thư mục này lên repository `phap-luat-daily`.
2. Vào **Settings → Secrets and variables → Actions → New repository secret**.
3. Tạo các secret:
   - `OPENAI_API_KEY`: API key OpenAI dùng để tóm tắt.
   - `SMTP_HOST`: máy chủ SMTP, ví dụ `smtp.gmail.com`.
   - `SMTP_PORT`: thường `587`.
   - `SMTP_USER`: email gửi.
   - `SMTP_PASSWORD`: mật khẩu ứng dụng SMTP (không dùng mật khẩu đăng nhập chính).
   - `MAIL_TO`: email nhận bản tin.
4. Vào **Actions**, chọn workflow **Pháp luật Daily**, bấm **Run workflow** để thử ngay.

## Lịch chạy

GitHub Actions dùng cron `0 1 * * *`, tương đương **08:00 UTC+7**.

Lưu ý: GitHub Actions có thể bắt đầu trễ vài phút so với lịch cron. Nếu cần đúng tuyệt đối 08:00 thì nên dùng scheduler chuyên dụng.

## Nội dung bản tin

Mặc định ưu tiên:
- Luật
- Nghị định
- Nghị quyết
- Pháp lệnh
- Thông tư
- Quyết định quan trọng

Bản tin gồm số hiệu, tên văn bản, cơ quan ban hành, ngày ban hành, ngày hiệu lực (nếu lấy được), tóm tắt và link nguồn.

## Ghi chú

Website có thể thay đổi cấu trúc HTML. Bộ crawler dùng cách dò tương đối linh hoạt, nhưng nếu Thư Viện Pháp Luật thay đổi giao diện thì cần cập nhật `src/crawler.py`.
