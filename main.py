"""
=================================================================
 LIBRARY MANAGEMENT SYSTEM
=================================================================
A command-line (CLI) library management application built with
Python + PostgreSQL.

This file contains ALL of the project's logic in a single file.
The code is organized into the following sections for easy
navigation:

    1) DATABASE CONNECTION       -> get_connection()
    2) BOOK CRUD OPERATIONS       -> BookRepository
    3) MEMBER CRUD OPERATIONS     -> MemberRepository
    4) LOAN OPERATIONS            -> LoanRepository
    5) CLI INTERFACE (MENUS)      -> *_menu() functions + main()

To run:
    python main.py

Database connection details are read from environment variables
(see the .env.example file).
=================================================================
"""

import os
import sys
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from tabulate import tabulate


# =================================================================
# 1) DATABASE CONNECTION
# =================================================================
# Connection details are never hardcoded; they are read from
# environment variables, so sensitive info such as passwords never
# gets pushed to GitHub (.env -> .gitignore).

class DatabaseConnectionError(Exception):
    """Custom exception raised when the database connection fails."""
    pass


def get_connection():
    """
    Connects to PostgreSQL and returns a connection object whose
    query results are dict-like (e.g. row['title'] access works).
    """
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "library_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    except psycopg2.OperationalError as exc:
        raise DatabaseConnectionError(f"Could not connect to the database: {exc}") from exc


# =================================================================
# 2) BOOK CRUD OPERATIONS
# =================================================================
# Create / Read / Update / Delete operations on the books table.

class BookRepository:
    def __init__(self, connection):
        self.connection = connection

    # ---- CREATE ----
    def add_book(self, title, author, isbn, genre, total_copies):
        """Adds a new book. available_copies starts out equal to total_copies."""
        query = """
            INSERT INTO books (title, author, isbn, genre, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING book_id;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (title, author, isbn, genre, total_copies, total_copies))
            book_id = cur.fetchone()["book_id"]
            self.connection.commit()
            return book_id

    # ---- READ ----
    def get_book_by_id(self, book_id):
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM books WHERE book_id = %s;", (book_id,))
            return cur.fetchone()

    def get_all_books(self):
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM books ORDER BY book_id;")
            return cur.fetchall()

    def search_books(self, keyword):
        """Searches for a keyword within title, author, or ISBN."""
        query = """
            SELECT * FROM books
            WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
            ORDER BY book_id;
        """
        like = f"%{keyword}%"
        with self.connection.cursor() as cur:
            cur.execute(query, (like, like, like))
            return cur.fetchall()

    # ---- UPDATE ----
    def update_book(self, book_id, title=None, author=None, genre=None, total_copies=None):
        """
        Updates only the fields that are provided (not None).
        If total_copies changes, available_copies is adjusted by the
        same delta (but never allowed to drop below 0).
        """
        current = self.get_book_by_id(book_id)
        if current is None:
            return False

        new_title = title if title is not None else current["title"]
        new_author = author if author is not None else current["author"]
        new_genre = genre if genre is not None else current["genre"]

        if total_copies is not None:
            diff = total_copies - current["total_copies"]
            new_total = total_copies
            new_available = max(0, current["available_copies"] + diff)
        else:
            new_total = current["total_copies"]
            new_available = current["available_copies"]

        query = """
            UPDATE books SET title=%s, author=%s, genre=%s,
                              total_copies=%s, available_copies=%s
            WHERE book_id=%s;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (new_title, new_author, new_genre,
                                 new_total, new_available, book_id))
            self.connection.commit()
            return cur.rowcount > 0

    # ---- DELETE ----
    def delete_book(self, book_id):
        with self.connection.cursor() as cur:
            cur.execute("DELETE FROM books WHERE book_id = %s;", (book_id,))
            self.connection.commit()
            return cur.rowcount > 0

    # ---- Helper methods (used by borrowing/returning to update stock) ----
    def decrement_available_copies(self, book_id):
        query = """
            UPDATE books SET available_copies = available_copies - 1
            WHERE book_id = %s AND available_copies > 0
            RETURNING book_id;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (book_id,))
            result = cur.fetchone()
            self.connection.commit()
            return result is not None

    def increment_available_copies(self, book_id):
        query = """
            UPDATE books SET available_copies = available_copies + 1
            WHERE book_id = %s AND available_copies < total_copies
            RETURNING book_id;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (book_id,))
            result = cur.fetchone()
            self.connection.commit()
            return result is not None


# =================================================================
# 3) MEMBER CRUD OPERATIONS
# =================================================================
# Create / Read / Update / Delete operations on the members table.

class MemberRepository:
    def __init__(self, connection):
        self.connection = connection

    # ---- CREATE ----
    def add_member(self, full_name, email, phone=None):
        query = """
            INSERT INTO members (full_name, email, phone)
            VALUES (%s, %s, %s) RETURNING member_id;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (full_name, email, phone))
            member_id = cur.fetchone()["member_id"]
            self.connection.commit()
            return member_id

    # ---- READ ----
    def get_member_by_id(self, member_id):
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM members WHERE member_id = %s;", (member_id,))
            return cur.fetchone()

    def get_all_members(self):
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM members ORDER BY member_id;")
            return cur.fetchall()

    def search_members(self, keyword):
        query = """
            SELECT * FROM members WHERE full_name ILIKE %s OR email ILIKE %s
            ORDER BY member_id;
        """
        like = f"%{keyword}%"
        with self.connection.cursor() as cur:
            cur.execute(query, (like, like))
            return cur.fetchall()

    # ---- UPDATE ----
    def update_member(self, member_id, full_name=None, email=None, phone=None, is_active=None):
        current = self.get_member_by_id(member_id)
        if current is None:
            return False

        new_name = full_name if full_name is not None else current["full_name"]
        new_email = email if email is not None else current["email"]
        new_phone = phone if phone is not None else current["phone"]
        new_active = is_active if is_active is not None else current["is_active"]

        query = """
            UPDATE members SET full_name=%s, email=%s, phone=%s, is_active=%s
            WHERE member_id=%s;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (new_name, new_email, new_phone, new_active, member_id))
            self.connection.commit()
            return cur.rowcount > 0

    # ---- DELETE ----
    def delete_member(self, member_id):
        with self.connection.cursor() as cur:
            cur.execute("DELETE FROM members WHERE member_id = %s;", (member_id,))
            self.connection.commit()
            return cur.rowcount > 0


# =================================================================
# 4) LOAN OPERATIONS
# =================================================================
# Business logic that involves the loans table joined with
# books/members (borrowing a book, returning a book, stock checks).

class LoanError(Exception):
    """Carries business-rule errors raised during borrow/return operations."""
    pass


class LoanRepository:
    DEFAULT_LOAN_DAYS = 14

    def __init__(self, connection, book_repository):
        self.connection = connection
        self.book_repository = book_repository

    # ---- CREATE (borrow a book) ----
    def borrow_book(self, book_id, member_id, loan_days=DEFAULT_LOAN_DAYS):
        """Checks stock, decrements it, and creates a new ACTIVE loan record."""
        book = self.book_repository.get_book_by_id(book_id)
        if book is None:
            raise LoanError(f"No book found with ID {book_id}.")
        if book["available_copies"] <= 0:
            raise LoanError(f"No available copies of '{book['title']}'.")

        if not self.book_repository.decrement_available_copies(book_id):
            raise LoanError("Could not update book stock.")

        due_date = date.today() + timedelta(days=loan_days)
        query = """
            INSERT INTO loans (book_id, member_id, due_date, status)
            VALUES (%s, %s, %s, 'ACTIVE') RETURNING loan_id;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (book_id, member_id, due_date))
            loan_id = cur.fetchone()["loan_id"]
            self.connection.commit()
            return loan_id

    # ---- UPDATE (return a book) ----
    def return_book(self, loan_id):
        """Marks the loan as RETURNED and increments the book's available stock."""
        loan = self.get_loan_by_id(loan_id)
        if loan is None:
            raise LoanError(f"No loan found with ID {loan_id}.")
        if loan["status"] == "RETURNED":
            raise LoanError("This book has already been returned.")

        query = """
            UPDATE loans SET status='RETURNED', return_date=CURRENT_TIMESTAMP
            WHERE loan_id=%s;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (loan_id,))
            self.connection.commit()

        self.book_repository.increment_available_copies(loan["book_id"])
        return True

    # ---- READ ----
    def get_loan_by_id(self, loan_id):
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM loans WHERE loan_id = %s;", (loan_id,))
            return cur.fetchone()

    def get_active_loans(self):
        """JOIN: returns active loans together with the book title and member name."""
        query = """
            SELECT l.loan_id, b.title, m.full_name, l.loan_date, l.due_date, l.status
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            WHERE l.status = 'ACTIVE'
            ORDER BY l.due_date;
        """
        with self.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_overdue_loans(self):
        """JOIN: loans that are still ACTIVE but past their due_date."""
        query = """
            SELECT l.loan_id, b.title, m.full_name, l.loan_date, l.due_date
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            WHERE l.status = 'ACTIVE' AND l.due_date < CURRENT_DATE
            ORDER BY l.due_date;
        """
        with self.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_loans_by_member(self, member_id):
        query = """
            SELECT l.loan_id, b.title, l.loan_date, l.due_date, l.return_date, l.status
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            WHERE l.member_id = %s
            ORDER BY l.loan_date DESC;
        """
        with self.connection.cursor() as cur:
            cur.execute(query, (member_id,))
            return cur.fetchall()

    def get_all_loans(self):
        query = """
            SELECT l.loan_id, b.title, m.full_name, l.loan_date,
                   l.due_date, l.return_date, l.status
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            ORDER BY l.loan_id DESC;
        """
        with self.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


# =================================================================
# 5) CLI INTERFACE (MENUS)
# =================================================================
# Handles all interaction with the user via the terminal.
# Calls the repository classes above; no SQL knowledge is needed here.

def print_header(text):
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50)


def print_table(rows):
    if not rows:
        print("(No records found)")
        return
    headers = list(rows[0].keys())
    table_data = [list(row.values()) for row in rows]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def prompt(text, required=True, cast=str):
    while True:
        value = input(text).strip()
        if not value and not required:
            return None
        if not value and required:
            print("This field cannot be empty.")
            continue
        try:
            return cast(value)
        except ValueError:
            print("Invalid value, please try again.")


# ---- 5a) Book menu ----
def book_menu(book_repo):
    while True:
        print_header("BOOK MANAGEMENT")
        print("1. Add Book\n2. List All Books\n3. Search Books"
              "\n4. Update Book\n5. Delete Book\n0. Back to Main Menu")
        choice = input("Your choice: ").strip()

        if choice == "1":
            title = prompt("Title: ")
            author = prompt("Author: ")
            isbn = prompt("ISBN: ")
            genre = prompt("Genre (optional): ", required=False)
            total_copies = prompt("Total copies: ", cast=int)
            try:
                book_id = book_repo.add_book(title, author, isbn, genre, total_copies)
                print(f"Book added. ID: {book_id}")
            except Exception as exc:
                print(f"Error: {exc}")

        elif choice == "2":
            print_table(book_repo.get_all_books())

        elif choice == "3":
            keyword = prompt("Search keyword (title/author/ISBN): ")
            print_table(book_repo.search_books(keyword))

        elif choice == "4":
            book_id = prompt("ID of the book to update: ", cast=int)
            if book_repo.get_book_by_id(book_id) is None:
                print("No book found with that ID.")
                continue
            print("(Leave fields blank if you don't want to change them)")
            title = prompt("New title: ", required=False)
            author = prompt("New author: ", required=False)
            genre = prompt("New genre: ", required=False)
            total_str = prompt("New total copies: ", required=False)
            total_copies = int(total_str) if total_str else None
            success = book_repo.update_book(book_id, title, author, genre, total_copies)
            print("Updated." if success else "Update failed.")

        elif choice == "5":
            book_id = prompt("ID of the book to delete: ", cast=int)
            if input(f"Book {book_id} will be deleted. Are you sure? (y/n): ").strip().lower() == "y":
                print("Deleted." if book_repo.delete_book(book_id) else "Book not found.")

        elif choice == "0":
            break
        else:
            print("Invalid choice.")


# ---- 5b) Member menu ----
def member_menu(member_repo):
    while True:
        print_header("MEMBER MANAGEMENT")
        print("1. Add Member\n2. List All Members\n3. Search Members"
              "\n4. Update Member\n5. Delete Member\n0. Back to Main Menu")
        choice = input("Your choice: ").strip()

        if choice == "1":
            full_name = prompt("Full name: ")
            email = prompt("Email: ")
            phone = prompt("Phone (optional): ", required=False)
            try:
                member_id = member_repo.add_member(full_name, email, phone)
                print(f"Member added. ID: {member_id}")
            except Exception as exc:
                print(f"Error: {exc}")

        elif choice == "2":
            print_table(member_repo.get_all_members())

        elif choice == "3":
            keyword = prompt("Search keyword (name/email): ")
            print_table(member_repo.search_members(keyword))

        elif choice == "4":
            member_id = prompt("ID of the member to update: ", cast=int)
            if member_repo.get_member_by_id(member_id) is None:
                print("No member found with that ID.")
                continue
            print("(Leave fields blank if you don't want to change them)")
            full_name = prompt("New full name: ", required=False)
            email = prompt("New email: ", required=False)
            phone = prompt("New phone: ", required=False)
            success = member_repo.update_member(member_id, full_name, email, phone)
            print("Updated." if success else "Update failed.")

        elif choice == "5":
            member_id = prompt("ID of the member to delete: ", cast=int)
            if input(f"Member {member_id} will be deleted. Are you sure? (y/n): ").strip().lower() == "y":
                print("Deleted." if member_repo.delete_member(member_id) else "Member not found.")

        elif choice == "0":
            break
        else:
            print("Invalid choice.")


# ---- 5c) Loan menu ----
def loan_menu(loan_repo):
    while True:
        print_header("LOAN MANAGEMENT")
        print("1. Borrow a Book\n2. Return a Book\n3. List Active Loans"
              "\n4. List Overdue Loans\n5. Show a Member's Loan History"
              "\n6. List All Loans\n0. Back to Main Menu")
        choice = input("Your choice: ").strip()

        if choice == "1":
            book_id = prompt("Book ID: ", cast=int)
            member_id = prompt("Member ID: ", cast=int)
            try:
                loan_id = loan_repo.borrow_book(book_id, member_id)
                print(f"Book borrowed successfully. Loan ID: {loan_id}")
            except LoanError as exc:
                print(f"Error: {exc}")

        elif choice == "2":
            loan_id = prompt("Loan ID to return: ", cast=int)
            try:
                loan_repo.return_book(loan_id)
                print("Book returned successfully.")
            except LoanError as exc:
                print(f"Error: {exc}")

        elif choice == "3":
            print_table(loan_repo.get_active_loans())

        elif choice == "4":
            print_table(loan_repo.get_overdue_loans())

        elif choice == "5":
            member_id = prompt("Member ID: ", cast=int)
            print_table(loan_repo.get_loans_by_member(member_id))

        elif choice == "6":
            print_table(loan_repo.get_all_loans())

        elif choice == "0":
            break
        else:
            print("Invalid choice.")


# ---- 5d) Main menu / entry point ----
def main():
    try:
        connection = get_connection()
    except DatabaseConnectionError as exc:
        print(f"\nCould not connect to the database:\n{exc}")
        print("\nPlease check your environment variables: "
              "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)

    book_repo = BookRepository(connection)
    member_repo = MemberRepository(connection)
    loan_repo = LoanRepository(connection, book_repo)

    try:
        while True:
            print_header("LIBRARY MANAGEMENT SYSTEM")
            print("1. Book Management\n2. Member Management\n3. Loan Management\n0. Exit")
            choice = input("Your choice: ").strip()

            if choice == "1":
                book_menu(book_repo)
            elif choice == "2":
                member_menu(member_repo)
            elif choice == "3":
                loan_menu(loan_repo)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
