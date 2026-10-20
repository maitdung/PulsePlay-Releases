# PulsePlay Releases

Kênh phát hành PulsePlay do maitdung quản lý.

[Tải bản mới nhất](https://github.com/maitdung/PulsePlay-Releases/releases/latest) · [Hướng dẫn phát hành](PUBLISHING.md) · [Kiểm tra quy trình tự động](https://github.com/maitdung/PulsePlay-Releases/actions/workflows/publish-update.yml)

## Đăng một bản mới

1. Build IPA mới với số build tăng lên. Ví dụ bản 315 dùng tag `v0.12.1-build315`.
2. Vào Releases → Draft a new release. Điền tag và tên bản cập nhật.
3. Ghi nội dung với các mục `## Tính năng mới`, `## Sửa lỗi`, `## Cải thiện hiệu năng`, `## Lưu ý`.
4. Đính kèm IPA rồi nhấn Publish release.
5. Chờ workflow Publish PulsePlay update feed hiện dấu xanh. App sẽ đọc phiên bản/build, dung lượng và nội dung bản mới từ nguồn cố định.

Workflow đã chạy thành công cho build 314. Các lần sau không cần tự sửa update.json hay altsource.json. Khi không đổi số phiên bản, vẫn phải tăng số build; không thay IPA khác nội dung cùng build.

## Người dùng app

Cài build 314 một lần để có giao diện và địa chỉ kênh cập nhật mới. Các bản trước chưa được gắn địa chỉ này nên không tự biết có bản mới trên GitHub.

App kiểm tra khi mở/hoạt động trở lại, có giới hạn tần suất; người dùng có thể bấm Kiểm tra bản mới. Nút Cập nhật tải IPA trong PulsePlay, hiển thị tiến trình, kiểm tra SHA-256 rồi mở bảng chia sẻ để chuyển sang bộ ký/cài. Có thêm đường cài trực tiếp bằng SideStore. Phần cài đặt vẫn cần bộ ký/cài tương thích; đây chưa phải tự cài hoàn toàn trong PulsePlay.

## Địa chỉ cố định

- Nguồn PulsePlay: https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/update.json
- Nguồn SideStore: https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/altsource.json

Không đưa tài khoản Apple, chứng chỉ ký hoặc log cá nhân lên repo.
