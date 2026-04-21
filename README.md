# Codex-Demos

Restaurant customer feedback demo application.

## Features

- Capture customer feedback with table number, rating, comments, and recommendation intent.
- View feedback entries in reverse-chronological order.
- Generate a quick summary with average rating and recommendation percentage.
- Includes a command-line interface for restaurant staff.

## Quick start

```bash
python3 restaurant_feedback_app.py
```

Follow the prompt to submit feedback, view entries, and view summary statistics.

## Programmatic usage

```python
from restaurant_feedback_app import RestaurantFeedbackApp

app = RestaurantFeedbackApp()
app.submit_feedback(
    customer_name="Avery",
    table_number=12,
    rating=5,
    comments="Excellent service and dessert.",
    would_recommend=True,
)

print(app.list_feedback())
print(app.get_feedback_summary())
app.close()
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```
