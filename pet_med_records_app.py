"""Pet digital medical records management application.

This module provides a small SQLite-backed application layer for:
- pet profiles
- vaccination schedules
- medical records
- appointment scheduling (including urgent appointments)
- veterinarian and specialist catalogs
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import sqlite3
from typing import Any


@dataclass(frozen=True)
class Pet:
    id: int
    name: str
    species: str
    breed: str
    birth_date: str
    owner_name: str
    owner_phone: str


@dataclass(frozen=True)
class Veterinarian:
    id: int
    name: str
    specialty: str
    is_specialist: bool
    phone: str


class PetMedicalRecordApp:
    """SQLite-backed service for managing pet medical workflows."""

    def __init__(self, db_path: str = "pet_medical_records.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        self.conn.close()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                owner_phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS veterinarians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                is_specialist INTEGER NOT NULL CHECK (is_specialist IN (0, 1)),
                phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vaccinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER NOT NULL,
                vaccine_name TEXT NOT NULL,
                due_date TEXT NOT NULL,
                administered_date TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY (pet_id) REFERENCES pets(id)
            );

            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER NOT NULL,
                record_date TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                treatment TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (pet_id) REFERENCES pets(id)
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_id INTEGER NOT NULL,
                veterinarian_id INTEGER NOT NULL,
                appointment_time TEXT NOT NULL,
                reason TEXT NOT NULL,
                urgent INTEGER NOT NULL CHECK (urgent IN (0, 1)),
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (pet_id) REFERENCES pets(id),
                FOREIGN KEY (veterinarian_id) REFERENCES veterinarians(id)
            );
            """
        )
        self.conn.commit()

    def add_pet(
        self,
        name: str,
        species: str,
        breed: str,
        birth_date: str,
        owner_name: str,
        owner_phone: str,
    ) -> int:
        self._validate_iso_date(birth_date)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO pets (name, species, breed, birth_date, owner_name, owner_phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, species, breed, birth_date, owner_name, owner_phone),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_veterinarian(
        self, name: str, specialty: str, is_specialist: bool, phone: str
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO veterinarians (name, specialty, is_specialist, phone)
            VALUES (?, ?, ?, ?)
            """,
            (name, specialty, int(is_specialist), phone),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_veterinarians(self, specialist_only: bool = False) -> list[Veterinarian]:
        cur = self.conn.cursor()
        if specialist_only:
            cur.execute(
                "SELECT id, name, specialty, is_specialist, phone FROM veterinarians WHERE is_specialist = 1 ORDER BY name"
            )
        else:
            cur.execute(
                "SELECT id, name, specialty, is_specialist, phone FROM veterinarians ORDER BY name"
            )

        return [
            Veterinarian(
                id=row["id"],
                name=row["name"],
                specialty=row["specialty"],
                is_specialist=bool(row["is_specialist"]),
                phone=row["phone"],
            )
            for row in cur.fetchall()
        ]

    def list_specialist_veterinarians(self) -> list[Veterinarian]:
        return self.list_veterinarians(specialist_only=True)

    def add_vaccination(
        self,
        pet_id: int,
        vaccine_name: str,
        due_date: str,
        administered_date: str | None = None,
    ) -> int:
        self._ensure_pet_exists(pet_id)
        due = self._validate_iso_date(due_date)
        administered = None
        if administered_date:
            administered = self._validate_iso_date(administered_date)

        status = self._vaccination_status(due, administered)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO vaccinations (pet_id, vaccine_name, due_date, administered_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pet_id,
                vaccine_name,
                due.isoformat(),
                administered.isoformat() if administered else None,
                status,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_vaccination_schedule(
        self, pet_id: int, days_ahead: int = 30
    ) -> list[dict[str, Any]]:
        self._ensure_pet_exists(pet_id)
        today = date.today()
        end = today + timedelta(days=days_ahead)
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, vaccine_name, due_date, administered_date, status
            FROM vaccinations
            WHERE pet_id = ?
              AND due_date BETWEEN ? AND ?
            ORDER BY due_date
            """,
            (pet_id, today.isoformat(), end.isoformat()),
        )

        return [dict(row) for row in cur.fetchall()]

    def add_medical_record(
        self,
        pet_id: int,
        record_date: str,
        diagnosis: str,
        treatment: str,
        notes: str = "",
    ) -> int:
        self._ensure_pet_exists(pet_id)
        self._validate_iso_date(record_date)

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO medical_records (pet_id, record_date, diagnosis, treatment, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pet_id, record_date, diagnosis, treatment, notes),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_pet_medical_history(self, pet_id: int) -> list[dict[str, Any]]:
        self._ensure_pet_exists(pet_id)
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, record_date, diagnosis, treatment, notes
            FROM medical_records
            WHERE pet_id = ?
            ORDER BY record_date DESC
            """,
            (pet_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def schedule_appointment(
        self,
        pet_id: int,
        veterinarian_id: int,
        appointment_time: str,
        reason: str,
        urgent: bool = False,
    ) -> int:
        self._ensure_pet_exists(pet_id)
        self._ensure_vet_exists(veterinarian_id)
        self._validate_iso_datetime(appointment_time)

        status = "queued-urgent" if urgent else "scheduled"
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO appointments (
                pet_id,
                veterinarian_id,
                appointment_time,
                reason,
                urgent,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pet_id,
                veterinarian_id,
                appointment_time,
                reason,
                int(urgent),
                status,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def create_urgent_appointment(
        self, pet_id: int, veterinarian_id: int, appointment_time: str, reason: str
    ) -> int:
        return self.schedule_appointment(
            pet_id=pet_id,
            veterinarian_id=veterinarian_id,
            appointment_time=appointment_time,
            reason=reason,
            urgent=True,
        )

    def get_appointments(self, urgent_first: bool = True) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        order = "urgent DESC, appointment_time ASC" if urgent_first else "appointment_time ASC"
        cur.execute(
            f"""
            SELECT a.id, a.pet_id, p.name AS pet_name, a.veterinarian_id, v.name AS veterinarian_name,
                   a.appointment_time, a.reason, a.urgent, a.status
            FROM appointments a
            JOIN pets p ON p.id = a.pet_id
            JOIN veterinarians v ON v.id = a.veterinarian_id
            ORDER BY {order}
            """
        )
        return [dict(row) for row in cur.fetchall()]

    def _ensure_pet_exists(self, pet_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM pets WHERE id = ?", (pet_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Pet with id={pet_id} does not exist.")

    def _ensure_vet_exists(self, veterinarian_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM veterinarians WHERE id = ?", (veterinarian_id,))
        if cur.fetchone() is None:
            raise ValueError(f"Veterinarian with id={veterinarian_id} does not exist.")

    @staticmethod
    def _validate_iso_date(value: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO date: {value}") from exc

    @staticmethod
    def _validate_iso_datetime(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO datetime: {value}") from exc

    @staticmethod
    def _vaccination_status(due: date, administered: date | None) -> str:
        if administered:
            return "completed"
        return "overdue" if due < date.today() else "pending"


if __name__ == "__main__":
    app = PetMedicalRecordApp()

    pet_id = app.add_pet(
        name="Luna",
        species="Dog",
        breed="Labrador",
        birth_date="2021-04-01",
        owner_name="J. Smith",
        owner_phone="+1-555-0100",
    )
    vet_general = app.add_veterinarian("Dr. Riley", "General Practice", False, "+1-555-1000")
    vet_specialist = app.add_veterinarian("Dr. Kim", "Cardiology", True, "+1-555-2000")

    app.add_vaccination(pet_id, "Rabies", (date.today() + timedelta(days=10)).isoformat())
    app.add_medical_record(
        pet_id,
        record_date=date.today().isoformat(),
        diagnosis="Seasonal allergy",
        treatment="Antihistamine",
        notes="Follow up in 2 weeks.",
    )
    app.schedule_appointment(
        pet_id,
        vet_general,
        (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat(),
        "Routine checkup",
    )
    app.create_urgent_appointment(
        pet_id,
        vet_specialist,
        (datetime.now() + timedelta(hours=4)).replace(microsecond=0).isoformat(),
        "Possible heart murmur",
    )

    print("Specialists:", app.list_specialist_veterinarians())
    print("Vaccines due soon:", app.get_vaccination_schedule(pet_id))
    print("Appointments:", app.get_appointments())
    app.close()
