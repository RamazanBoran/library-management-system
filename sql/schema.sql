-- ============================================================
-- Library Management System - Database Schema
-- Database: PostgreSQL
-- ============================================================

-- Uncomment if you want to reset existing tables (use with caution!)
-- DROP TABLE IF EXISTS loans CASCADE;
-- DROP TABLE IF EXISTS books CASCADE;
-- DROP TABLE IF EXISTS members CASCADE;

-- ------------------------------------------------------------
-- Table: books
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id         SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    author          VARCHAR(255) NOT NULL,
    isbn            VARCHAR(20) UNIQUE NOT NULL,
    genre           VARCHAR(100),
    total_copies    INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    added_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_copies CHECK (available_copies <= total_copies)
);

-- ------------------------------------------------------------
-- Table: members
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id       SERIAL PRIMARY KEY,
    full_name       VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    joined_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- Table: loans
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS loans (
    loan_id         SERIAL PRIMARY KEY,
    book_id         INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    member_id       INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    loan_date       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date        DATE NOT NULL,
    return_date     TIMESTAMP,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE', 'RETURNED', 'OVERDUE'))
);

-- ------------------------------------------------------------
-- Indexes for performance
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
CREATE INDEX IF NOT EXISTS idx_members_email ON members (email);
CREATE INDEX IF NOT EXISTS idx_loans_book_id ON loans (book_id);
CREATE INDEX IF NOT EXISTS idx_loans_member_id ON loans (member_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans (status);
