# Phát hành PulsePlay

Nơi phát hành: https://github.com/maitdung/PulsePlay-Releases/releases

Nguồn app kiểm tra cố định:
https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/update.json

Nguồn SideStore:
https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/altsource.json

## Mỗi lần có bản mới

1. Tăng build trong app và widget, build/kiểm tra IPA.
2. Tạo GitHub Release với tag khớp IPA: ví dụ `v0.12.1-build315`.
3. Điền nội dung: `## Tính năng mới`, `## Sửa lỗi`, `## Cải thiện hiệu năng`,
   `## Lưu ý`. Nội dung này sẽ hiện trong PulsePlay.
4. Đính kèm IPA trước khi nhấn Publish release.
5. Workflow `Publish PulsePlay update feed` tạo nguồn cập nhật, dung lượng,
   SHA-256 và đính kèm metadata. Kiểm tra Actions xanh và mở link update.json.
   Lần đầu cần đính kèm icon.png; những lần sau workflow dùng lại icon phát hành.
6. Nếu workflow lỗi, không thông báo bản mới đã sẵn sàng. Sửa lỗi rồi chạy
   workflow thủ công với đúng tag. Không thay IPA khác nội dung cùng build.

Repo chỉ chứa gói phát hành và công cụ tạo nguồn; không cần đưa mã app,
tài khoản Apple hay chứng chỉ ký của người dùng lên GitHub.

## Người dùng

Các bản cũ không chứa địa chỉ kênh cập nhật phải cài build 314 một lần.
Từ đó app kiểm tra địa chỉ cố định, so phiên bản + build rồi hiện chi tiết.
Nút Cập nhật tải IPA trong app, có hủy và kiểm tra SHA-256. Sau đó mở bảng
chia sẻ để chuyển file sang ứng dụng ký/cài. Nút cài trực tiếp SideStore
chuyển URL IPA cho SideStore tải và ký trên iPhone.

Đây chưa phải tự cài hoàn toàn trong PulsePlay. iOS vẫn yêu cầu bộ ký/cài
phù hợp và có thể yêu cầu xác nhận. Thiết lập SideStore lần đầu riêng; kênh
GitHub không tự gia hạn chữ ký và không thay thế cơ chế ký của iOS.
Không cần người dùng tự lên GitHub tìm IPA cho các lần cập nhật sau.
