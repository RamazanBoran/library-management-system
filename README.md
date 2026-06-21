# Library Management System

A command-line (CLI) library management system built with Python and
PostgreSQL. Supports full CRUD (Create, Read, Update, Delete) operations
for books, members, and loans.

This project was built as part of the internship program's **Phase 2 -
Project 1 (Library Management System)** requirements, using the
**Python + SQL + GitHub** technology stack.

---

## Technologies Used

| Technology   | Purpose                                      |
|--------------|------------------------------------------------|
| Python 3.10+ | Application logic and CLI interface             |
| PostgreSQL   | Data storage (books, members, loan records)     |
| psycopg2     | Python - PostgreSQL connection                  |
| tabulate     | Table-formatted output in the CLI               |
| pytest       | Automated test cases                            |

---

## Features

- **Book Management:** Add, list, search (title/author/ISBN), update, delete
- **Member Management:** Add, list, search (name/email), update, delete
- **Loan Management:**
  - Borrow a book (with stock check)
  - Return a book (stock updated automatically)
  - List active / overdue loans
  - View a member's loan history
- **Data integrity:** Stock counts are enforced at the database level via `CHECK` constraints.
- **JOIN queries:** Loan records are joined with book and member info for meaningful reports.

---

## Project Structure

The code lives in a **single file** (`main.py`) for simplicity, but is
organized into clearly labeled sections:

```
library-management-system/
├── main.py            # Entire app: DB connection + CRUD + CLI menus
├── test_main.py        # All tests (pytest)
├── sql/
│   ├── schema.sql       # Database table schema
│   └── seed_data.sql    # Optional sample data
├── .env.example         # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

Sections inside `main.py` (marked with comments):

1. **Database Connection** — `get_connection()`
2. **Book CRUD** — `BookRepository` class
3. **Member CRUD** — `MemberRepository` class
4. **Loan Operations** — `LoanRepository` class (JOIN queries, stock checks)
5. **CLI Interface** — `*_menu()` functions and `main()`

---

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd library-management-system
```

### 2. Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up the PostgreSQL database
```bash
psql -U postgres -c "CREATE DATABASE library_db;"
psql -U postgres -d library_db -f sql/schema.sql
```

(Optional) load sample data:
```bash
psql -U postgres -d library_db -f sql/seed_data.sql
```

### 5. Configure environment variables
```bash
cp .env.example .env
```
Then edit `.env` with your own credentials, or export them directly in
your terminal:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=library_db
export DB_USER=postgres
export DB_PASSWORD=postgres
```

---

## Running the App

```bash
python main.py
```

```
==================================================
LIBRARY MANAGEMENT SYSTEM
==================================================
1. Book Management
2. Member Management
3. Loan Management
0. Exit
Your choice:
```

---

## Running the Tests

Tests run against a **real PostgreSQL database** and truncate the tables
before each test. Use a **separate test database**:

```bash
psql -U postgres -c "CREATE DATABASE library_db_test;"
psql -U postgres -d library_db_test -f sql/schema.sql
export DB_NAME=library_db_test
```

```bash
pytest test_main.py -v
```

Expected output:
```
============================= test session starts ==============================
collected 21 items

test_main.py ......................                                      [100%]

============================== 21 passed in 1.18s ===============================
```

> Do **not** run the tests against your production database — it
> truncates the tables and your data will be lost.

---

## Database Schema

```
books                          members                       loans
─────────────────────         ────────────────────         ──────────────────────
book_id (PK)                   member_id (PK)                loan_id (PK)
title                          full_name                     book_id (FK → books)
author                         email (UNIQUE)                 member_id (FK → members)
isbn (UNIQUE)                  phone                          loan_date
genre                          joined_at                      due_date
total_copies                   is_active                      return_date
available_copies                                              status (ACTIVE/RETURNED)
added_at
```

---

## Key Design Decisions

- **Repository Pattern:** Database queries (`BookRepository`, `MemberRepository`,
  `LoanRepository`) are kept separate from the CLI, making the logic easy
  to test and maintain.
- **Stock safety:** `borrow_book()` checks stock first, then updates
  `available_copies` atomically; a `LoanError` is raised when no copies
  are available.
- **Data integrity:** The `available_copies <= total_copies` constraint
  is enforced at the database level (`CHECK` constraint).
- **Security:** Database credentials are never hardcoded; they're managed
  via environment variables (`.env`, excluded via `.gitignore`).

---

## Note

This project was built as part of the internship program's **Phase 1 -
DataCamp courses** (Data Literacy, Python Data Fundamentals, Java
Fundamentals, SQL Data Fundamentals, GitHub Foundations), followed by
**Phase 2 - Project Development**.
---

## Development Process

I started this project by designing the database schema (books, members,
and loans tables, along with the relationships between them). I then built
a Repository Pattern in Python that connects to PostgreSQL — using a
separate class for each table (BookRepository, MemberRepository,
LoanRepository) to keep the SQL queries cleanly separated from the CLI.
Finally, I wrote 21 test cases with pytest covering each CRUD operation.

## Challenges I Faced

Setting up the virtual environment correctly was a bit confusing at first —
packages were initially installed into the global Python environment
instead of inside a virtual environment, which I had to fix by recreating
the venv and reinstalling the dependencies inside it. I also had to be
careful with the stock count (`available_copies`) logic, making sure it
stays consistent when books are borrowed and returned.

## What I Learned

- How to connect Python to PostgreSQL using psycopg2
- How to enforce data integrity at the database level using CHECK constraints
- How to use JOIN queries to build meaningful reports across multiple tables
- How to write automated tests with pytest
- How to use Git/GitHub for version control and keep credentials secure with .env

## The Role of Python, SQL, and GitHub in This Project

- **Python:** Handles all of the application's business logic — CRUD
  operations, stock checks, and the CLI interface.
- **SQL (PostgreSQL):** Stores all the data; CHECK and FOREIGN KEY
  constraints enforce data integrity at the database level.
- **GitHub:** The entire development process was tracked through version
  control, and the source code and documentation were shared publicly here.