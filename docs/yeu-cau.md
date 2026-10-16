# Yêu cầu — Mượn sách giữa sinh viên

## Tác nhân

| Tác nhân | Là ai | Muốn gì từ hệ thống |
|---|---|---|
| Sinh viên mượn sách | Sinh viên muốn mượn sách từ sinh viên khác | Tìm sách phù hợp và gửi yêu cầu mượn |
| Sinh viên cho mượn sách | Sinh viên đăng ký sách mình sở hữu | Quản lý sách và xử lý yêu cầu mượn |
| Thành viên quản lý hệ thống | Người phụ trách vận hành và hỗ trợ hệ thống | Theo dõi dữ liệu và xử lý vấn đề phát sinh |

## Yêu cầu chức năng

Viết dạng: Là [tác nhân], tôi muốn [làm gì] để [đạt gì].

| # | Tác nhân | Muốn | Để |
|---|---|---|---|
| FR-01 | Sinh viên cho mượn sách | đăng ký sách mình sở hữu, bao gồm thông tin sách | những sinh viên khác có thể tìm thấy sách để mượn |
| FR-02 | Sinh viên mượn sách | tìm kiếm sách đã đăng ký theo tên sách hoặc thông tin liên quan | tìm được sách phù hợp với nhu cầu |
| FR-03 | Sinh viên mượn sách | gửi yêu cầu mượn một cuốn sách còn khả dụng | đề nghị chủ sở hữu cho mượn sách |
| FR-04 | Sinh viên cho mượn sách | xem các yêu cầu mượn sách gửi đến mình | biết ai đang muốn mượn sách của mình |
| FR-05 | Sinh viên cho mượn sách | chấp nhận hoặc từ chối một yêu cầu mượn | chủ động quyết định việc cho mượn |
| FR-06 | Sinh viên mượn sách và sinh viên cho mượn sách | xem trạng thái yêu cầu và quá trình mượn-trả | theo dõi được yêu cầu đã gửi và tình trạng sách |

## Yêu cầu phi chức năng

Các ngưỡng dưới đây là **mục tiêu đề xuất để nhóm xác nhận**, không phải kết quả đo thực tế.

| # | Chỉ số | Ngưỡng | Điều kiện đo | Ảnh hưởng tới thiết kế nào |
|---|---|---|---|---|
| NFR-01 | Thời gian phản hồi tìm kiếm | 95% lượt tìm kiếm hoàn thành trong ≤ 2 giây | Đo khi có 50 lượt tìm kiếm liên tiếp trên bộ dữ liệu thử nghiệm gồm 500 cuốn sách | Thiết kế truy vấn tìm kiếm và cách hiển thị kết quả |
| NFR-02 | Tính toàn vẹn dữ liệu sau tải lại trang | 100% dữ liệu sách và yêu cầu đã lưu vẫn còn sau 10 lần tải lại trang | Tạo sách và yêu cầu thử nghiệm, tải lại trang 10 lần rồi đối chiếu dữ liệu | Thiết kế lưu trữ dữ liệu và xử lý cập nhật |
| NFR-03 | Khả năng sử dụng trên màn hình nhỏ | Giao diện không tràn chiều ngang ở độ rộng từ 320 px trở lên | Kiểm tra 3 lần tại độ rộng 320 px, 375 px và 768 px | Thiết kế bố cục responsive và thành phần giao diện |

## Ràng buộc nghiệp vụ — điều KHÔNG được phép xảy ra

| # | Ràng buộc | Ai chịu trách nhiệm bảo vệ (lớp nào, điền ở M3) |
|---|---|---|
| BR-01 | Không được gửi yêu cầu mượn đối với sách không khả dụng hoặc đang được cho mượn theo trạng thái hiện tại | Chưa xác định — bổ sung ở M3 |
| BR-02 | Không được chấp nhận yêu cầu không còn hợp lệ hoặc thực hiện chuyển trạng thái mượn-trả không phù hợp với trạng thái hiện tại | Chưa xác định — bổ sung ở M3 |

## Câu hỏi còn mở cho khách hàng

- Sinh viên cần cung cấp những thông tin nào khi đăng ký một cuốn sách?
- Khi nhiều sinh viên cùng muốn mượn một cuốn sách, hệ thống nên xử lý các yêu cầu như thế nào?
- Hai bên thống nhất thời gian và cách thức giao-trả sách bằng cách nào?
- Sinh viên có được hủy yêu cầu sau khi chủ sở hữu đã chấp nhận không? Nếu có, điều kiện hủy là gì?
- Khi sách bị mất hoặc hư hỏng trong thời gian mượn, hai bên cần xử lý như thế nào?