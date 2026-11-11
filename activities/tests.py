from datetime import date, timedelta

from activities.models import ExerciseType, Medication, NutritionLog
from core.testing.api import ApiTestCase


class RouteFixTests(ApiTestCase):
    """Routes the app calls with a trailing slash / UUID ids."""

    def test_hydration_by_date(self):
        self.post('hydration/hydration/', {
            'date': '2026-01-05', 'amount_ml': 500})
        res = self.get('hydration/hydration/2026-01-05/')
        self.assertEqual(res.status_code, 200, res.content)

    def test_nutrition_update_delete(self):
        log = NutritionLog.objects.create(
            customer=self.customer, date=date.today(), name='Oats')
        res = self.put(f'nutrition/logs/{log.id}/', {
            'date': str(date.today()), 'name': 'Oatmeal'})
        self.assertEqual(res.status_code, 200, res.content)
        res = self.delete(f'nutrition/logs/{log.id}/')
        self.assertEqual(res.status_code, 200, res.content)

    def test_medication_update_delete_with_uuid(self):
        med = Medication.objects.create(
            customer=self.customer, name='Folic acid', dosage='400mcg')
        res = self.put(f'medication/medications/{med.id}/', {
            'name': 'Folic acid', 'dosage': '800mcg',
            'frequency_period': 'daily', 'times_per_period': 1})
        self.assertEqual(res.status_code, 200, res.content)
        res = self.delete(f'medication/medications/{med.id}/')
        self.assertEqual(res.status_code, 200, res.content)


class ExerciseTests(ApiTestCase):

    def test_types_seeded(self):
        res = self.get('exercise/types/?category=Cardio')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json())
        self.assertTrue(all(t['category'] == 'Cardio' for t in res.json()))

    def test_log_and_week_summary(self):
        walk = ExerciseType.objects.get(name='Brisk Walk')
        today = date.today()
        res = self.post('exercise/logs/', {
            'exercise_type_id': walk.id, 'date': str(today), 'minutes': 30})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertGreater(res.json()['calories'], 0)  # estimated
        # outside this week: must not count
        self.post('exercise/logs/', {
            'name': 'Old run', 'date': str(today - timedelta(days=8)),
            'minutes': 60})

        res = self.get(f'exercise/summary/{today}/')
        body = res.json()
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(body['totals']['minutes'], 30)
        self.assertEqual(body['progress']['minutes'], 20.0)

        log_id = body['logs'][0]['id']
        self.assertEqual(self.delete(f'exercise/logs/{log_id}/').status_code, 200)


class SleepTests(ApiTestCase):

    def test_upsert_list_delete(self):
        today = str(date.today())
        self.post('sleep/logs/', {'date': today, 'duration_hours': 6})
        res = self.post('sleep/logs/', {
            'date': today, 'duration_hours': 7.5, 'quality': 'Excellent'})
        self.assertEqual(res.status_code, 200, res.content)

        body = self.get('sleep/logs/').json()
        self.assertEqual(len(body['entries']), 1)
        self.assertEqual(body['entries'][0]['duration_hours'], 7.5)
        self.assertEqual(body['stats']['average_hours_7d'], 7.5)

        res = self.delete(f"sleep/logs/{body['entries'][0]['id']}/")
        self.assertEqual(res.status_code, 200)

    def test_rejects_bad_duration(self):
        res = self.post('sleep/logs/', {
            'date': str(date.today()), 'duration_hours': 30})
        self.assertEqual(res.status_code, 422)
