-- ============================================================
-- Library Management System - Sample Seed Data
-- This file is optional; use it to try out the system with
-- some pre-populated records.
-- ============================================================

INSERT INTO books (title, author, isbn, genre, total_copies, available_copies) VALUES
    ('Crime and Punishment', 'Fyodor Dostoevsky', '9789750718533', 'Fiction', 3, 3),
    ('1984', 'George Orwell', '9789750718540', 'Dystopian', 4, 4),
    ('Les Misérables', 'Victor Hugo', '9789750718557', 'Fiction', 2, 2),
    ('Clean Code', 'Robert C. Martin', '9780132350884', 'Software', 5, 5),
    ('Sapiens', 'Yuval Noah Harari', '9780062316097', 'History', 3, 3)
ON CONFLICT (isbn) DO NOTHING;

INSERT INTO members (full_name, email, phone) VALUES
    ('Jane Smith', 'jane.smith@example.com', '555-111-2233'),
    ('Emily Clark', 'emily.clark@example.com', '555-222-3344'),
    ('John Doe', 'john.doe@example.com', '555-333-4455')
ON CONFLICT (email) DO NOTHING;
