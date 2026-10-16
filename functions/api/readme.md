# API Functions

## 1. Mục đích

Thư mục `functions/api/` chứa các Cloudflare Pages Functions của hệ thống mượn sách.

Mỗi file hoặc thư mục trong đây tương ứng với một API route.

```text
functions/api/books.js
    -> GET /api/books

functions/api/books/available.js
    -> GET /api/books/available

functions/api/borrow-requests.js
    -> POST /api/borrow-requests
```

## 2. Kiến trúc

```text
Frontend
    |
    | HTTP request
    v
functions/api
    |
    | xử lý request, validate dữ liệu
    v
functions/lib
    |
    | kết nối Supabase
    v
PostgreSQL
```

### Các thư mục liên quan

```text
functions/
├── api/
│   ├── README.md
│   ├── books.js
│   ├── books/
│   │   └── available.js
│   └── borrow-requests.js
│
└── lib/
    ├── db.js
    └── http.js
```

- `api/`: định nghĩa endpoint.
- `lib/db.js`: tạo Supabase client.
- `lib/http.js`: xử lý JSON response, CORS và request body.
- API không được chứa secret trong source code.

## 3. Environment variables

Backend cần các biến môi trường:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_...
ALLOWED_ORIGIN=http://localhost:8788
```

Có thể dùng key cũ trong quá trình chuyển đổi:

```env
SUPABASE_SERVICE_ROLE_KEY=...
```

`SUPABASE_SECRET_KEY` hoặc `SUPABASE_SERVICE_ROLE_KEY` chỉ được sử dụng trong backend.

Không đưa các key này vào:

```text
src/
src/data/data.js
index.html
```

## 4. API lấy danh sách sách

### Endpoint

```http
GET /api/books
```

Mặc định trả về sách có trạng thái `AVAILABLE`.

### Lọc theo trạng thái

```http
GET /api/books?status=AVAILABLE
```

Các trạng thái hợp lệ:

```text
AVAILABLE
RESERVED
ON_LOAN
INACTIVE
```

### Response thành công

HTTP status:

```http
200 OK
```

```json
{
  "success": true,
  "books": [
    {
      "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "ownerUserId": "11111111-1111-1111-1111-111111111111",
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "isbn": null,
      "description": null,
      "status": "AVAILABLE",
      "createdAt": "2026-10-13T10:00:00Z"
    }
  ]
}
```

### Lỗi status không hợp lệ

HTTP status:

```http
400 Bad Request
```

```json
{
  "success": false,
  "code": "INVALID_BOOK_STATUS",
  "message": "Invalid book status"
}
```

## 5. API lấy sách khả dụng

### Endpoint

```http
GET /api/books/available
```

Đây là alias của:

```http
GET /api/books?status=AVAILABLE
```

API chỉ trả về các sách có:

```text
status = AVAILABLE
```

## 6. API tạo borrow request

### Endpoint

```http
POST /api/borrow-requests
Content-Type: application/json
```

### Request body

Trong phiên bản hiện tại:

```json
{
  "bookId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "userId": "22222222-2222-2222-2222-222222222222"
}
```

`bookId` phải là UUID của sách.

`userId` phải là UUID của user tồn tại trong bảng `users`.

### Quy trình xử lý

Backend thực hiện:

```text
1. Kiểm tra bookId và userId.
2. Kiểm tra user tồn tại.
3. Kiểm tra user đang ACTIVE.
4. Kiểm tra số lần trả trễ của user.
5. Kiểm tra sách tồn tại.
6. Kiểm tra user không phải chủ sách.
7. Kiểm tra sách có status AVAILABLE.
8. Kiểm tra request PENDING bị trùng.
9. Tạo borrow request với status PENDING.
10. Trả về borrow request vừa tạo.
```

### Response thành công

HTTP status:

```http
201 Created
```

```json
{
  "success": true,
  "message": "Borrow request created successfully",
  "borrowRequest": {
    "id": "request-uuid",
    "bookId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "borrowerUserId": "22222222-2222-2222-2222-222222222222",
    "status": "PENDING",
    "requestedAt": "2026-10-13T10:30:00Z"
  }
}
```

### Các lỗi có thể xảy ra

#### Thiếu dữ liệu

```http
400 Bad Request
```

```json
{
  "success": false,
  "code": "INVALID_REQUEST",
  "message": "bookId and userId are required"
}
```

#### Không tìm thấy user

```http
404 Not Found
```

```json
{
  "success": false,
  "code": "USER_NOT_FOUND",
  "message": "User does not exist"
}
```

#### User bị khóa

```http
403 Forbidden
```

```json
{
  "success": false,
  "code": "USER_BLOCKED",
  "message": "User is not allowed to borrow books"
}
```

#### Không tìm thấy sách

```http
404 Not Found
```

```json
{
  "success": false,
  "code": "BOOK_NOT_FOUND",
  "message": "Book does not exist"
}
```

#### Mượn sách của chính mình

```http
409 Conflict
```

```json
{
  "success": false,
  "code": "CANNOT_BORROW_OWN_BOOK",
  "message": "You cannot borrow your own book"
}
```

#### Sách không khả dụng

```http
409 Conflict
```

```json
{
  "success": false,
  "code": "BOOK_UNAVAILABLE",
  "message": "This book is not available for borrowing"
}
```

#### Request trùng

```http
409 Conflict
```

```json
{
  "success": false,
  "code": "DUPLICATE_BORROW_REQUEST",
  "message": "You already have a pending request for this book"
}
```

## 7. API kiểm tra borrow request

API này cần bổ sung `onRequestGet` trong file `borrow-requests.js`.

### Endpoint đề xuất

```http
GET /api/borrow-requests?userId=USER_UUID
```

API trả về các request của một user:

```json
{
  "success": true,
  "borrowRequests": [
    {
      "id": "request-uuid",
      "bookId": "book-uuid",
      "borrowerUserId": "user-uuid",
      "status": "PENDING",
      "requestedAt": "2026-10-13T10:30:00Z"
    }
  ]
}
```

Các trạng thái borrow request:

```text
PENDING
APPROVED
REJECTED
CANCELLED
EXPIRED
```

Hiện tại hệ thống mới có flow tạo request nên request mới sẽ luôn có:

```text
status = PENDING
```

## 8. Kiểm tra API local

Khởi động Pages Functions:

```powershell
npx wrangler pages dev src --env-file .env --port 8788
```

Test lấy sách:

```powershell
curl.exe -i http://localhost:8788/api/books
```

Test lấy sách khả dụng:

```powershell
curl.exe -i http://localhost:8788/api/books/available
```

Test tạo borrow request bằng PowerShell:

```powershell
$body = @{
    bookId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    userId = "22222222-2222-2222-2222-222222222222"
} | ConvertTo-Json -Compress

Invoke-RestMethod `
    -Uri "http://localhost:8788/api/borrow-requests" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Kiểm tra request của user:

```powershell
Invoke-RestMethod `
    -Uri "http://localhost:8788/api/borrow-requests?userId=22222222-2222-2222-2222-222222222222" `
    -Method Get
```

## 9. Database requirements

Trước khi test API, database phải có:

```text
users
books
borrow_requests
```

Dữ liệu test phải thỏa mãn:

```text
user tồn tại
user.account_status = ACTIVE
user.late_return_count < 3
book tồn tại
book.status = AVAILABLE
user không phải owner của book
```

## 10. Quy tắc bảo mật

Phiên bản hiện tại nhận `userId` từ request body hoặc query để phục vụ việc test.

Khi thêm authentication, không nên tin `userId` từ frontend.

Thay vào đó:

```text
1. Frontend gửi Authorization token.
2. Backend xác thực token.
3. Backend lấy user ID từ token.
4. Backend bỏ qua userId do client gửi.
```

Các API cần trả về lỗi JSON thống nhất:

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "Human-readable error message"
}
```