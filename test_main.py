"""
=================================================================
 TESTS - Library Management System
=================================================================
Collects all tests for the repository classes in main.py
(Book/Member/Loan) into a single file. Sections:

    1) FIXTURES (test setup)
    2) BOOK CRUD TESTS
    3) MEMBER CRUD TESTS
    4) LOAN TESTS

To run (from the project root directory):
    pytest test_main.py -v

NOTE: Tests connect to a real PostgreSQL database and truncate the
tables before every test. For this reason, it is recommended to use
a separate test database (see README.md).
=================================================================
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from main import (  # noqa: E402
    get_connection,
    BookRepository,
    MemberRepository,
    LoanRepository,
    LoanError,
)


# =================================================================
# 1) FIXTURES
# =================================================================
@pytest.fixture
def connection():
    """Provides a fresh connection with empty tables for each test."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE loans, books, members RESTART IDENTITY CASCADE;")
    conn.commit()
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def book_repo(connection):
    return BookRepository(connection)


@pytest.fixture
def member_repo(connection):
    return MemberRepository(connection)


@pytest.fixture
def loan_repo(connection, book_repo):
    return LoanRepository(connection, book_repo)


# =================================================================
# 2) BOOK CRUD TESTS
# =================================================================
def test_add_book_creates_record(book_repo):
    book_id = book_repo.add_book("Test Book", "Test Author", "1111111111111", "Fiction", 3)
    book = book_repo.get_book_by_id(book_id)
    assert book["title"] == "Test Book"
    assert book["total_copies"] == 3
    assert book["available_copies"] == 3


def test_get_all_books_returns_all_records(book_repo):
    book_repo.add_book("Book A", "Author A", "1111111111111", "Fiction", 1)
    book_repo.add_book("Book B", "Author B", "2222222222222", "Science", 2)
    assert len(book_repo.get_all_books()) == 2


def test_search_books_by_title_or_author(book_repo):
    book_repo.add_book("Learning Python", "Jane Smith", "1111111111111", "Software", 1)
    book_repo.add_book("Java Handbook", "John Doe", "2222222222222", "Software", 1)

    assert len(book_repo.search_books("Python")) == 1
    assert len(book_repo.search_books("Smith")) == 1


def test_update_book_changes_only_given_fields(book_repo):
    book_id = book_repo.add_book("Old Title", "Author", "1111111111111", "Fiction", 2)
    success = book_repo.update_book(book_id, title="New Title")
    updated = book_repo.get_book_by_id(book_id)

    assert success is True
    assert updated["title"] == "New Title"
    assert updated["author"] == "Author"  # should remain unchanged


def test_update_book_adjusts_available_copies(book_repo):
    book_id = book_repo.add_book("Book", "Author", "1111111111111", "Fiction", 2)
    book_repo.update_book(book_id, total_copies=5)
    updated = book_repo.get_book_by_id(book_id)
    assert updated["total_copies"] == 5
    assert updated["available_copies"] == 5  # no copies had been borrowed yet


def test_update_book_returns_false_for_missing_id(book_repo):
    assert book_repo.update_book(9999, title="Nonexistent") is False


def test_delete_book_removes_record(book_repo):
    book_id = book_repo.add_book("To Be Deleted", "Author", "1111111111111", "Fiction", 1)
    assert book_repo.delete_book(book_id) is True
    assert book_repo.get_book_by_id(book_id) is None


def test_decrement_available_copies_respects_zero_floor(book_repo):
    book_id = book_repo.add_book("Single Copy", "Author", "1111111111111", "Fiction", 1)
    assert book_repo.decrement_available_copies(book_id) is True
    assert book_repo.decrement_available_copies(book_id) is False  # stock is already 0


# =================================================================
# 3) MEMBER CRUD TESTS
# =================================================================
def test_add_member_creates_record(member_repo):
    member_id = member_repo.add_member("Jane Smith", "jane@example.com", "555-111-2233")
    member = member_repo.get_member_by_id(member_id)
    assert member["full_name"] == "Jane Smith"
    assert member["is_active"] is True


def test_get_all_members_returns_all_records(member_repo):
    member_repo.add_member("Member A", "membera@example.com")
    member_repo.add_member("Member B", "memberb@example.com")
    assert len(member_repo.get_all_members()) == 2


def test_search_members_by_name_or_email(member_repo):
    member_repo.add_member("Jane Smith", "jane.unique@example.com")
    member_repo.add_member("John Doe", "john@example.com")

    assert len(member_repo.search_members("Jane")) == 1
    assert len(member_repo.search_members("unique")) == 1


def test_update_member_changes_only_given_fields(member_repo):
    member_id = member_repo.add_member("Old Name", "old@example.com")
    success = member_repo.update_member(member_id, full_name="New Name")
    updated = member_repo.get_member_by_id(member_id)

    assert success is True
    assert updated["full_name"] == "New Name"
    assert updated["email"] == "old@example.com"  # should remain unchanged


def test_update_member_returns_false_for_missing_id(member_repo):
    assert member_repo.update_member(9999, full_name="Nonexistent") is False


def test_delete_member_removes_record(member_repo):
    member_id = member_repo.add_member("To Be Deleted", "delete@example.com")
    assert member_repo.delete_member(member_id) is True
    assert member_repo.get_member_by_id(member_id) is None


# =================================================================
# 4) LOAN TESTS
# =================================================================
@pytest.fixture
def sample_book(book_repo):
    return book_repo.add_book("Test Book", "Test Author", "1111111111111", "Fiction", 2)


@pytest.fixture
def sample_member(member_repo):
    return member_repo.add_member("Test Member", "test@example.com")


def test_borrow_book_creates_loan_and_decrements_stock(
    loan_repo, book_repo, sample_book, sample_member
):
    loan_id = loan_repo.borrow_book(sample_book, sample_member)
    loan = loan_repo.get_loan_by_id(loan_id)
    book = book_repo.get_book_by_id(sample_book)

    assert loan["status"] == "ACTIVE"
    assert book["available_copies"] == 1  # dropped from 2 to 1


def test_borrow_book_fails_when_no_stock(loan_repo, book_repo, member_repo):
    book_id = book_repo.add_book("Single Copy", "Author", "2222222222222", "Fiction", 1)
    member1 = member_repo.add_member("Member 1", "member1@example.com")
    member2 = member_repo.add_member("Member 2", "member2@example.com")

    loan_repo.borrow_book(book_id, member1)  # stock 1 -> 0
    with pytest.raises(LoanError):
        loan_repo.borrow_book(book_id, member2)  # no stock left


def test_borrow_book_fails_for_nonexistent_book(loan_repo, sample_member):
    with pytest.raises(LoanError):
        loan_repo.borrow_book(9999, sample_member)


def test_return_book_marks_returned_and_restores_stock(
    loan_repo, book_repo, sample_book, sample_member
):
    loan_id = loan_repo.borrow_book(sample_book, sample_member)
    assert loan_repo.return_book(loan_id) is True

    loan = loan_repo.get_loan_by_id(loan_id)
    book = book_repo.get_book_by_id(sample_book)
    assert loan["status"] == "RETURNED"
    assert book["available_copies"] == 2  # restored


def test_return_book_fails_if_already_returned(loan_repo, sample_book, sample_member):
    loan_id = loan_repo.borrow_book(sample_book, sample_member)
    loan_repo.return_book(loan_id)
    with pytest.raises(LoanError):
        loan_repo.return_book(loan_id)


def test_get_active_loans_excludes_returned(loan_repo, sample_book, sample_member):
    loan_id = loan_repo.borrow_book(sample_book, sample_member)
    assert len(loan_repo.get_active_loans()) == 1

    loan_repo.return_book(loan_id)
    assert len(loan_repo.get_active_loans()) == 0


def test_get_loans_by_member_returns_history(loan_repo, book_repo, sample_member):
    book1 = book_repo.add_book("Book 1", "Author", "3333333333333", "Fiction", 1)
    book2 = book_repo.add_book("Book 2", "Author", "4444444444444", "Fiction", 1)
    loan_repo.borrow_book(book1, sample_member)
    loan_repo.borrow_book(book2, sample_member)

    assert len(loan_repo.get_loans_by_member(sample_member)) == 2
