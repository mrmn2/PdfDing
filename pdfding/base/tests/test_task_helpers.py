from base import task_helpers
from django.test import TestCase


class TestTaskHelpers(TestCase):
    def test_parse_cron_schedule(self):
        expected_dict = {'minute': '3', 'hour': '*/2', 'day': '6', 'month': '7', 'day_of_week': '*'}
        generated_dict = task_helpers.parse_cron_schedule('3 */2 6 7 *')

        self.assertEqual(expected_dict, generated_dict)
