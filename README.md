# Codex-Demos

Digital medical records demo application for pets.

## Features

- Register pets and owner information.
- Maintain vaccination records and retrieve upcoming vaccine schedules.
- Store longitudinal medical records per pet.
- Schedule regular appointments.
- Create urgent appointments that are prioritized in retrieval.
- Maintain a catalog of veterinarians and specialist veterinarians.

## Quick start

```bash
python3 pet_med_records_app.py
```

The script seeds a small demo and prints specialists, upcoming vaccines, and appointments.

## Programmatic usage

```python
from pet_med_records_app import PetMedicalRecordApp

app = PetMedicalRecordApp()
pet_id = app.add_pet("Luna", "Dog", "Labrador", "2021-04-01", "J. Smith", "+1-555-0100")
vet_id = app.add_veterinarian("Dr. Riley", "General Practice", False, "+1-555-1000")

app.add_vaccination(pet_id, "Rabies", "2026-01-01")
app.add_medical_record(pet_id, "2025-05-10", "Otitis", "Ear drops", "Monitor for 10 days")
app.schedule_appointment(pet_id, vet_id, "2026-01-03T09:00:00", "Routine checkup")

print(app.get_vaccination_schedule(pet_id, days_ahead=90))
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```
