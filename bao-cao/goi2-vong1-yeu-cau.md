# Gói 2 — Vòng 1: Yêu cầu

## 1. Nhóm đã thực hiện

Nhóm xây dựng hệ thống mượn sách giữa sinh viên. Sinh viên có thể đăng ký sách mình sở hữu, tìm sách và gửi yêu cầu mượn. Người sở hữu sách xem xét và xử lý yêu cầu. Hệ thống cần theo dõi trạng thái sách và lượt mượn, đồng thời từ chối các thao tác không phù hợp với trạng thái hiện tại.

Tài liệu yêu cầu: `docs/yeu-cau.md`.

Luồng chính và trạng thái cần được đối chiếu với mã nguồn hiện tại trước khi xác nhận mức độ hoàn thành. URL triển khai được ghi trong README: [https://se100.pages.dev/](https://se100.pages.dev/)

## 2. Ba quyết định thiết kế chính

### Quyết định 1 — Phân biệt người mượn và người cho mượn

Người mượn gửi yêu cầu; người sở hữu sách quyết định xử lý yêu cầu. Cách phân chia này làm rõ trách nhiệm của từng tác nhân.

### Quyết định 2 — Theo dõi trạng thái của lượt mượn

Lượt mượn phải có trạng thái rõ ràng để hệ thống xác định thao tác nào được phép thực hiện tiếp theo. Không được chấp nhận thao tác mâu thuẫn với trạng thái hiện tại.

### Quyết định 3 — Ngăn mượn sách không khả dụng

Hệ thống cần kiểm tra tình trạng sách trước khi chấp nhận yêu cầu mượn, tránh để một cuốn sách được cho nhiều người mượn cùng lúc.

## 3. Kiểm tra kết quả do công cụ hỗ trợ tạo ra

### Lần kiểm tra 1 — Kiểm tra luật gửi yêu cầu mượn

- **Nội dung kiểm tra:** Các điều kiện được định nghĩa trong `src/service/borrowRules.js`.
- **Cách kiểm tra:** Đọc mã nguồn và đối chiếu các nhánh điều kiện với yêu cầu nghiệp vụ.
- **Kết quả:** Mã nguồn có kiểm tra sách và người dùng không tồn tại, tài khoản không hoạt động hoặc có từ 3 lần trả trễ, sách không ở trạng thái `AVAILABLE`, và trường hợp người dùng mượn sách của chính mình. Đây là kết quả kiểm tra bằng cách đọc mã nguồn; chưa phải kết quả chạy kiểm thử tự động.

### Lần kiểm tra 2 — Đối chiếu quy tắc nghiệp vụ với lược đồ cơ sở dữ liệu

- **Nội dung kiểm tra:** Cấu trúc bảng `books`, `borrow_requests` và các ràng buộc trong `supabase/migrations/001_initial.sql`.
- **Cách kiểm tra:** Đọc mã SQL và đối chiếu các trạng thái, khóa ngoại, ràng buộc `CHECK` và chỉ mục với yêu cầu nghiệp vụ.
- **Kết quả:** Lược đồ giới hạn các trạng thái hợp lệ của sách và yêu cầu mượn; các khóa ngoại liên kết yêu cầu mượn với sách và người dùng; chỉ mục duy nhất có điều kiện ngăn một người dùng tạo nhiều yêu cầu `PENDING` cho cùng một cuốn sách. Tuy nhiên, chỉ mục này không ngăn nhiều người dùng khác nhau cùng gửi yêu cầu `PENDING` cho một cuốn sách. Chưa xác minh được cơ chế xử lý đồng thời và các luật nghiệp vụ khác ở phía backend. Đây là kết quả đối chiếu mã nguồn SQL, chưa phải kết quả kiểm thử thực thi.

## 4. Hồi cứu vòng 1

- Điều nhóm đã làm được: đã có tài liệu yêu cầu và các tài liệu tiến độ vòng 1 trong kho.
- Điều cần cải thiện: cần kiểm tra tính nhất quán giữa yêu cầu, tài liệu, mã nguồn và luồng chạy thực tế.
- Bước tiếp theo: hoàn thiện bằng chứng kiểm tra, xác nhận luồng chính trên URL triển khai và cập nhật các tài liệu còn thiếu.