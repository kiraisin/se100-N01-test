# Database ERD

Sơ đồ dưới đây mô tả quan hệ giữa người dùng, sách, borrow request, lượt mượn, vi phạm và lịch sử trạng thái.

```mermaid
erDiagram
    USERS ||--o{ BOOKS : owns
    USERS ||--o{ BORROW_REQUESTS : creates
    BOOKS ||--o{ BORROW_REQUESTS : receives

    BORROW_REQUESTS ||--o| LOANS : creates

    USERS ||--o{ LOANS : lends
    USERS ||--o{ LOANS : borrows

    USERS ||--o{ VIOLATIONS : receives
    LOANS ||--o{ VIOLATIONS : causes

    BOOKS ||--o{ BOOK_STATUS_HISTORIES : has
    BORROW_REQUESTS ||--o{ BORROW_REQUEST_STATUS_HISTORIES : has
    LOANS ||--o{ LOAN_STATUS_HISTORIES : has

    USERS {
        uuid id PK
        string student_code UK
        string full_name
        string email UK
        string role
        string account_status
        int late_return_count
        datetime created_at
        datetime updated_at
    }

    BOOKS {
        uuid id PK
        uuid owner_user_id FK
        string title
        string author
        string isbn
        string description
        string status
        datetime created_at
        datetime updated_at
    }

    BORROW_REQUESTS {
        uuid id PK
        uuid book_id FK
        uuid borrower_user_id FK
        string status
        datetime requested_at
        datetime reviewed_at
        uuid reviewed_by FK
        string review_note
    }

    LOANS {
        uuid id PK
        uuid request_id FK UK
        uuid book_id FK
        uuid lender_user_id FK
        uuid borrower_user_id FK
        string status
        datetime handed_at
        datetime due_at
        datetime returned_at
        datetime created_at
    }

    VIOLATIONS {
        uuid id PK
        uuid user_id FK
        uuid loan_id FK
        string description
        datetime created_at
        datetime resolved_at
    }

    BOOK_STATUS_HISTORIES {
        uuid id PK
        uuid book_id FK
        string old_status
        string new_status
        uuid changed_by FK
        string reason
        datetime created_at
    }

    BORROW_REQUEST_STATUS_HISTORIES {
        uuid id PK
        uuid borrow_request_id FK
        string old_status
        string new_status
        uuid changed_by FK
        string reason
        datetime created_at
    }

    LOAN_STATUS_HISTORIES {
        uuid id PK
        uuid loan_id FK
        string old_status
        string new_status
        uuid changed_by FK
        string reason
        datetime created_at
    }
```