from datetime import timedelta

from django.test import SimpleTestCase

from bigboy.reviews.services.scheduling import MAX_INTERVAL_DAYS, apply_grade, initial_review_timedelta


class ApplyGradeTests(SimpleTestCase):
    def test_again_resets_interval_and_repetitions(self):
        interval, reps, delta = apply_grade(grade='again', interval_days=10, repetitions=4)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)
        self.assertEqual(delta, timedelta(days=1))

    def test_good_scales_interval(self):
        interval, reps, delta = apply_grade(grade='good', interval_days=3, repetitions=0)
        self.assertEqual(reps, 1)
        self.assertEqual(interval, 6)
        self.assertEqual(delta, timedelta(days=6))

    def test_hard_increases_less_than_good(self):
        good_i, _, _ = apply_grade(grade='good', interval_days=4, repetitions=0)
        hard_i, _, _ = apply_grade(grade='hard', interval_days=4, repetitions=0)
        self.assertLessEqual(hard_i, good_i)

    def test_easy_caps_at_max(self):
        interval, _, delta = apply_grade(grade='easy', interval_days=MAX_INTERVAL_DAYS, repetitions=0)
        self.assertLessEqual(interval, MAX_INTERVAL_DAYS)
        self.assertEqual(delta.days, interval)

    def test_initial_review_timedelta(self):
        self.assertEqual(initial_review_timedelta(), timedelta(days=1))
