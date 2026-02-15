from datetime import date, datetime, timedelta
import unittest

from pet_med_records_app import PetMedicalRecordApp


class PetMedicalRecordAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = PetMedicalRecordApp(":memory:")
        self.pet_id = self.app.add_pet(
            name="Milo",
            species="Cat",
            breed="Mixed",
            birth_date="2020-01-15",
            owner_name="Alex",
            owner_phone="555-0101",
        )
        self.vet_general = self.app.add_veterinarian(
            name="Dr. Green", specialty="General Practice", is_specialist=False, phone="555-1212"
        )
        self.vet_specialist = self.app.add_veterinarian(
            name="Dr. Heart", specialty="Cardiology", is_specialist=True, phone="555-1213"
        )

    def tearDown(self) -> None:
        self.app.close()

    def test_specialist_catalog_filters_correctly(self) -> None:
        specialists = self.app.list_specialist_veterinarians()
        self.assertEqual(len(specialists), 1)
        self.assertEqual(specialists[0].name, "Dr. Heart")

    def test_vaccination_schedule(self) -> None:
        due_soon = (date.today() + timedelta(days=5)).isoformat()
        outside_window = (date.today() + timedelta(days=90)).isoformat()

        self.app.add_vaccination(self.pet_id, "Rabies", due_soon)
        self.app.add_vaccination(self.pet_id, "Bordetella", outside_window)

        schedule = self.app.get_vaccination_schedule(self.pet_id, days_ahead=30)
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]["vaccine_name"], "Rabies")

    def test_medical_history_sorted_desc(self) -> None:
        self.app.add_medical_record(
            self.pet_id,
            record_date="2024-01-01",
            diagnosis="Cold",
            treatment="Rest",
        )
        self.app.add_medical_record(
            self.pet_id,
            record_date="2024-01-10",
            diagnosis="Recovered",
            treatment="None",
        )

        history = self.app.get_pet_medical_history(self.pet_id)
        self.assertEqual(history[0]["diagnosis"], "Recovered")
        self.assertEqual(history[1]["diagnosis"], "Cold")

    def test_urgent_appointment_prioritized(self) -> None:
        routine_time = (datetime.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
        urgent_time = (datetime.now() + timedelta(hours=1)).replace(microsecond=0).isoformat()

        self.app.schedule_appointment(
            self.pet_id,
            self.vet_general,
            routine_time,
            "Routine check",
            urgent=False,
        )
        self.app.create_urgent_appointment(
            self.pet_id,
            self.vet_specialist,
            urgent_time,
            "Trouble breathing",
        )

        appointments = self.app.get_appointments()
        self.assertEqual(appointments[0]["urgent"], 1)
        self.assertEqual(appointments[0]["status"], "queued-urgent")


if __name__ == "__main__":
    unittest.main()
