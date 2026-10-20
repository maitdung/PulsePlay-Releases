# PulsePlay Releases

Repo này phân phối IPA và công cụ cập nhật, **không chứa mã nguồn ứng dụng PulsePlay**. Không tải mã app, chứng chỉ hoặc khóa ký lên đây.

## Cách đăng bản mới đơn giản nhất

1. Build IPA với số build tăng lên.
2. [Mở trang tải IPA lên](https://github.com/maitdung/PulsePlay-Releases/upload/main/incoming), kéo IPA vào rồi chọn **Commit changes** lên main.
3. Đợi [Upload IPA to publish](https://github.com/maitdung/PulsePlay-Releases/actions/workflows/ipa-drop.yml) chạy xanh.

Hệ thống tự đọc phiên bản trong IPA, tạo Release và nguồn cập nhật. Không cần đặt tag hay sửa JSON thủ công. IPA trùng build và giống nội dung sẽ được bỏ qua; cùng build nhưng khác nội dung bị từ chối.

Muốn hiển thị chi tiết: tải cùng IPA một file như `v0.12.1-build315.md`, có các mục `## Tính năng mới`, `## Sửa lỗi`, `## Cải thiện hiệu năng`. Các mục có nội dung gạch đầu dòng. Không có file này thì chỉ hiện thông báo chung, không tự suy đoán sửa lỗi.

## Người dùng

Cần cài build 314 một lần để có kênh cập nhật. Từ đó app kiểm tra khi mở/hoạt động trở lại, có giới hạn tần suất; có thể bấm Kiểm tra bản mới. App hiển thị phiên bản, chi tiết và tải IPA có kiểm tra SHA-256. Cài đặt vẫn qua bộ ký/cài tương thích trên iPhone, không phải tự cài âm thầm trong PulsePlay.

[Tải bản mới nhất](https://github.com/maitdung/PulsePlay-Releases/releases/latest)

- Nguồn app: https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/update.json
- Nguồn SideStore: https://github.com/maitdung/PulsePlay-Releases/releases/latest/download/altsource.json

## Cách thủ công dự phòng

Tạo Release với tag khớp IPA, ví dụ `v0.12.1-build315`, đính kèm IPA, ghi thay đổi rồi Publish release. Workflow Publish PulsePlay update feed tạo metadata. Nếu workflow lỗi, xử lý lỗi và kiểm tra Actions xanh trước khi thông báo phát hành.
