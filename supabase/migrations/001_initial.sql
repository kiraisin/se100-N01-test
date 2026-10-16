CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    student_code VARCHAR(30) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,

    role VARCHAR(30) NOT NULL DEFAULT 'STUDENT'
        CHECK (role IN ('STUDENT', 'COORDINATOR', 'ADMIN')),

    account_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE'
        CHECK (account_status IN ('ACTIVE', 'INACTIVE')),

    late_return_count INTEGER NOT NULL DEFAULT 0
        CHECK (late_return_count >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    owner_user_id UUID NOT NULL
        REFERENCES users(id),

    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    isbn VARCHAR(30),
    description TEXT,

    status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (
            status IN (
                'AVAILABLE',
                'RESERVED',
                'ON_LOAN',
                'INACTIVE'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE borrow_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    book_id UUID NOT NULL
        REFERENCES books(id),

    borrower_user_id UUID NOT NULL
        REFERENCES users(id),

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'APPROVED',
                'REJECTED',
                'CANCELLED',
                'EXPIRED'
            )
        ),

    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    review_note TEXT
);

CREATE INDEX idx_books_status
ON books(status);

CREATE INDEX idx_books_owner
ON books(owner_user_id);

CREATE INDEX idx_borrow_requests_borrower
ON borrow_requests(borrower_user_id);

CREATE UNIQUE INDEX uq_pending_request_per_user_book
ON borrow_requests (borrower_user_id, book_id)
WHERE status = 'PENDING';