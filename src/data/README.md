# Database Design

## 1. Mục tiêu

Database phục vụ hệ thống chia sẻ và mượn sách giữa sinh viên.

Các nghiệp vụ chính:

- Người dùng đăng ký sách mình sở hữu.
- Người dùng xem và tìm kiếm sách.
- Người dùng gửi yêu cầu mượn sách.
- Backend kiểm tra sách có khả dụng hay không.
- Backend lưu yêu cầu với trạng thái `PENDING`.
- Sau này có thể duyệt, giao, trả sách và xử lý trả trễ.

## 2. Công nghệ đề xuất

Sử dụng PostgreSQL.

Lý do:

- Dữ liệu có quan hệ rõ ràng giữa người dùng, sách và borrow request.
- Hỗ trợ khóa ngoại và transaction.
- Có thể tạo unique index để chống request trùng.
- Có thể mở rộng thêm loan, violation và lịch sử trạng thái.
- Phù hợp với Supabase nếu frontend triển khai trên Cloudflare Pages.

Mật khẩu và thông tin đăng nhập không được lưu trong database nghiệp vụ. Có thể sử dụng Supabase Auth hoặc một authentication provider khác.

## 3. Các bảng

### 3.1. `users`

Lưu thông tin người dùng và người điều phối.

| Cột | Mô tả |
|---|---|
| `id` | Khóa chính |
| `student_code` | Mã sinh viên |
| `full_name` | Họ tên |
| `email` | Email |
| `role` | `STUDENT`, `COORDINATOR` hoặc `ADMIN` |
| `account_status` | `ACTIVE` hoặc `INACTIVE` |
| `late_return_count` | Số lần trả sách trễ |
| `created_at` | Thời điểm tạo |
| `updated_at` | Thời điểm cập nhật |

Sinh viên bị khóa tài khoản khi:

```text
late_return_count >= 3
```

### 3.2. `books`

Lưu sách được đăng ký trên hệ thống.

| Cột | Mô tả |
|---|---|
| `id` | Khóa chính |
| `owner_user_id` | Người sở hữu sách |
| `title` | Tên sách |
| `author` | Tác giả |
| `isbn` | Mã ISBN, có thể rỗng |
| `description` | Mô tả sách |
| `status` | Trạng thái sách |
| `created_at` | Thời điểm tạo |
| `updated_at` | Thời điểm cập nhật |

Các trạng thái:

```text
AVAILABLE    Có thể gửi yêu cầu mượn
RESERVED     Đã có request được chấp nhận
ON_LOAN      Đang được mượn
INACTIVE     Không còn cho mượn
```

### 3.3. `borrow_requests`

Lưu yêu cầu mượn sách.

| Cột | Mô tả |
|---|---|
| `id` | Khóa chính |
| `book_id` | Sách được yêu cầu |
| `borrower_user_id` | Người muốn mượn |
| `status` | Trạng thái request |
| `requested_at` | Thời điểm tạo |
| `reviewed_at` | Thời điểm xử lý |
| `reviewed_by` | Người xử lý |
| `review_note` | Ghi chú xử lý |

Các trạng thái:

```text
PENDING     Đang chờ xử lý
APPROVED    Đã được chấp nhận
REJECTED    Bị từ chối
CANCELLED   Người mượn hủy
EXPIRED     Hết hạn
```

Trong workflow hiện tại, request mới luôn có:

```text
status = PENDING
```

Khi tạo request `PENDING`, trạng thái sách vẫn giữ là `AVAILABLE` vì chưa có flow chấp nhận request.

### 3.4. `loans`

Lưu thông tin mượn thực tế. Bảng này chỉ được tạo bản ghi sau khi borrow request được chấp nhận.

| Cột | Mô tả |
|---|---|
| `id` | Khóa chính |
| `request_id` | Borrow request tương ứng |
| `book_id` | Sách được mượn |
| `lender_user_id` | Chủ sách |
| `borrower_user_id` | Người mượn |
| `status` | Trạng thái lượt mượn |
| `handed_at` | Ngày giao sách |
| `due_at` | Hạn trả |
| `returned_at` | Ngày trả thực tế |
| `created_at` | Thời điểm tạo |

Các trạng thái:

```text
WAITING_HANDOVER   Đã duyệt, chưa giao sách
ACTIVE              Đang được mượn
OVERDUE             Đã quá hạn
RETURNED            Đã trả
CANCELLED           Đã hủy
```

Một borrow request chỉ được tạo tối đa một loan.

### 3.5. `violations`

Lưu các vi phạm liên quan đến việc mượn sách.

| Cột | Mô tả |
|---|---|
| `id` | Khóa chính |
| `user_id` | Người vi phạm |
| `loan_id` | Lượt mượn liên quan |
| `description` | Mô tả |
| `created_at` | Thời điểm tạo |
| `resolved_at` | Thời điểm xử lý xong |

Các loại vi phạm:

```text
LATE_RETURN
```

### 3.6. Các bảng lịch sử trạng thái

Có thể sử dụng các bảng:

```text
book_status_histories
borrow_request_status_histories
loan_status_histories
```

Các bảng này lưu:

- Trạng thái cũ.
- Trạng thái mới.
- Người thực hiện.
- Thời điểm thay đổi.
- Lý do thay đổi.

## 4. Quy tắc dữ liệu

- `books.owner_user_id` phải tham chiếu đến một user hợp lệ.
- `borrow_requests.book_id` phải tham chiếu đến một sách hợp lệ.
- `borrow_requests.borrower_user_id` phải tham chiếu đến một user hợp lệ.
- Người dùng không được mượn sách do chính mình sở hữu.
- Người bị khóa không được tạo borrow request mới.
- Chỉ tạo request khi sách đang `AVAILABLE`.
- Một người không được có hai request `PENDING` cho cùng một sách.
- Một sách chỉ có tối đa một loan đang hoạt động.
- Một request chỉ tạo tối đa một loan.
- `returned_at` không được sớm hơn `handed_at`.
- `due_at` không được sớm hơn ngày giao sách.

Unique index đề xuất:

```sql
CREATE UNIQUE INDEX uq_pending_request_per_user_book
ON borrow_requests (borrower_user_id, book_id)
WHERE status = 'PENDING';
```

Một sách có thể có nhiều request `PENDING` từ nhiều người khác nhau. Khi một request được chấp nhận, các request còn lại có thể được chuyển sang `REJECTED` hoặc giữ lại tùy nghiệp vụ.

## 5. API hiện tại

### Lấy danh sách sách

```http
GET /api/books
```

### Lấy sách khả dụng

```http
GET /api/books?status=AVAILABLE
```

Có thể hỗ trợ thêm:

```http
GET /api/books/available
```

### Tạo borrow request

```http
POST /api/borrow-requests
Content-Type: application/json
```

Request body:

```json
{
  "bookId": "book-001"
}
```

`borrowerUserId` nên lấy từ token hoặc session ở backend. Không nên tin `userId` do frontend tự gửi nếu hệ thống đã có authentication.

Response thành công:

```http
201 Created
```

```json
{
  "success": true,
  "message": "Borrow request created successfully",
  "borrowRequest": {
    "id": "request-001",
    "bookId": "book-001",
    "borrowerUserId": "user-123",
    "status": "PENDING",
    "requestedAt": "2026-10-12T10:30:00Z"
  }
}
```

Response thất bại:

```json
{
  "success": false,
  "code": "BOOK_UNAVAILABLE",
  "message": "This book is not available for borrowing"
}
```

Các lỗi chính:

| HTTP status | Code |
|---:|---|
| 400 | `INVALID_REQUEST` |
| 401 | `UNAUTHORIZED` |
| 404 | `BOOK_NOT_FOUND` |
| 409 | `BOOK_UNAVAILABLE` |
| 409 | `DUPLICATE_BORROW_REQUEST` |
| 500 | `INTERNAL_ERROR` |

## 6. Transaction tạo borrow request

Backend nên thực hiện trong một transaction:

1. Xác thực người dùng.
2. Kiểm tra `bookId`.
3. Tìm sách.
4. Kiểm tra sách có trạng thái `AVAILABLE`.
5. Kiểm tra request `PENDING` bị trùng.
6. Insert borrow request với status `PENDING`.
7. Commit transaction.
8. Trả về bản ghi vừa lưu.

Không trả về request trước khi transaction commit thành công.