import unittest

from restaurant_feedback_app import RestaurantFeedbackApp


class RestaurantFeedbackAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = RestaurantFeedbackApp(":memory:")

    def tearDown(self) -> None:
        self.app.close()

    def test_submit_and_list_feedback(self) -> None:
        self.app.submit_feedback("Taylor", 7, 5, "Great service and food.", True)

        entries = self.app.list_feedback()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].customer_name, "Taylor")
        self.assertEqual(entries[0].rating, 5)
        self.assertTrue(entries[0].would_recommend)

    def test_summary_calculation(self) -> None:
        self.app.submit_feedback("Sam", 3, 4, "Nice ambience.", True)
        self.app.submit_feedback("Jordan", 5, 2, "Food arrived cold.", False)

        summary = self.app.get_feedback_summary()
        self.assertEqual(summary["total_entries"], 2.0)
        self.assertEqual(summary["average_rating"], 3.0)
        self.assertEqual(summary["recommend_percentage"], 50.0)

    def test_rating_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.app.submit_feedback("Casey", 2, 6, "Too loud.", False)


if __name__ == "__main__":
    unittest.main()
