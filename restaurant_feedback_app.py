"""Restaurant customer feedback interface.

This module provides a small SQLite-backed service and a CLI interface for
collecting restaurant customer feedback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True)
class FeedbackEntry:
    id: int
    customer_name: str
    table_number: int
    rating: int
    comments: str
    would_recommend: bool
    created_at: str


class RestaurantFeedbackApp:
    """SQLite-backed service for restaurant customer feedback."""

    def __init__(self, db_path: str = "restaurant_feedback.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        self.conn.close()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                table_number INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comments TEXT NOT NULL,
                would_recommend INTEGER NOT NULL CHECK (would_recommend IN (0, 1)),
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def submit_feedback(
        self,
        customer_name: str,
        table_number: int,
        rating: int,
        comments: str,
        would_recommend: bool,
    ) -> int:
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")
        if table_number < 1:
            raise ValueError("Table number must be a positive integer.")

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO feedback (
                customer_name,
                table_number,
                rating,
                comments,
                would_recommend,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                customer_name.strip() or "Anonymous",
                table_number,
                rating,
                comments.strip(),
                int(would_recommend),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_feedback(self) -> list[FeedbackEntry]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, customer_name, table_number, rating, comments, would_recommend, created_at
            FROM feedback
            ORDER BY created_at DESC
            """
        )
        return [
            FeedbackEntry(
                id=row["id"],
                customer_name=row["customer_name"],
                table_number=row["table_number"],
                rating=row["rating"],
                comments=row["comments"],
                would_recommend=bool(row["would_recommend"]),
                created_at=row["created_at"],
            )
            for row in cur.fetchall()
        ]

    def get_feedback_summary(self) -> dict[str, float]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_entries,
                COALESCE(AVG(rating), 0.0) AS average_rating,
                COALESCE(SUM(would_recommend), 0) AS recommend_count
            FROM feedback
            """
        )
        row = cur.fetchone()
        assert row is not None
        total = int(row["total_entries"])
        recommend_count = int(row["recommend_count"])
        return {
            "total_entries": float(total),
            "average_rating": round(float(row["average_rating"]), 2),
            "recommend_percentage": round((recommend_count / total) * 100, 2) if total else 0.0,
        }


def run_cli() -> None:
    app = RestaurantFeedbackApp()
    print("Welcome to the Restaurant Customer Feedback Interface")

    try:
        while True:
            print("\nChoose an option:")
            print("1) Submit feedback")
            print("2) View recent feedback")
            print("3) View summary")
            print("4) Exit")
            choice = input("Enter choice (1-4): ").strip()

            if choice == "1":
                name = input("Customer name: ").strip()
                table_number = int(input("Table number: ").strip())
                rating = int(input("Rating (1-5): ").strip())
                comments = input("Comments: ").strip()
                recommend_text = input("Would recommend? (y/n): ").strip().lower()
                would_recommend = recommend_text.startswith("y")

                feedback_id = app.submit_feedback(
                    customer_name=name,
                    table_number=table_number,
                    rating=rating,
                    comments=comments,
                    would_recommend=would_recommend,
                )
                print(f"Thank you! Your feedback id is {feedback_id}.")
            elif choice == "2":
                entries = app.list_feedback()
                if not entries:
                    print("No feedback entries yet.")
                    continue
                for entry in entries:
                    print(
                        f"[{entry.id}] {entry.customer_name} | Table {entry.table_number} | "
                        f"Rating {entry.rating}/5 | Recommend: {'Yes' if entry.would_recommend else 'No'}"
                    )
                    print(f"    {entry.comments}")
            elif choice == "3":
                summary = app.get_feedback_summary()
                print("Feedback summary:")
                print(f"- Total entries: {int(summary['total_entries'])}")
                print(f"- Average rating: {summary['average_rating']}/5")
                print(f"- Recommendation rate: {summary['recommend_percentage']}%")
            elif choice == "4":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please choose 1, 2, 3, or 4.")
    finally:
        app.close()


if __name__ == "__main__":
    run_cli()
