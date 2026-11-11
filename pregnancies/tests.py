from datetime import date, timedelta

from activities.models import HydrationLog, SleepLog
from core.testing.api import ApiTestCase
from customers.models import DailyEntry, WeightEntry
from pregnancies.models import Pregnancy


class DashboardTests(ApiTestCase):

    def test_404_without_pregnancy(self):
        self.assertEqual(self.get('pregnancy/dashboard/').status_code, 404)

    def test_dashboard(self):
        today = date.today()
        due = today + timedelta(days=280 - 24 * 7)  # week 24
        Pregnancy.objects.create(customer=self.customer, due_date=due)
        self.customer.height = 165
        self.customer.save()
        WeightEntry.objects.create(customer=self.customer, weight=60, unit='kg',
                                   entry_date=today - timedelta(weeks=26))
        WeightEntry.objects.create(customer=self.customer, weight=68, unit='kg',
                                   entry_date=today)
        HydrationLog.objects.create(customer=self.customer, date=today,
                                    amount_ml=1000, daily_goal_ml=2000)
        SleepLog.objects.create(customer=self.customer, date=today,
                                duration_hours=8)
        DailyEntry.objects.create(customer=self.customer, date=today,
                                  symptoms=['5'])

        res = self.get('pregnancy/dashboard/')
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        self.assertEqual(body['pregnancy']['current_week'], 24)
        self.assertEqual(body['pregnancy']['trimester'], 2)
        self.assertEqual(body['baby']['size_comparison'], 'cantaloupe')
        self.assertEqual(body['maternal']['weight_gain_kg'], 8.0)
        self.assertEqual(body['maternal']['recommended_gain'], '11.5-16 kg')
        self.assertEqual(body['today']['water_glasses'], 4.0)
        self.assertEqual(body['health_metrics']['sleep'], round(1 / 7, 2))
        self.assertEqual(body['recent_symptoms'][0]['name'], 'Headache')
        self.assertEqual(len(body['activity_last_7_days']), 7)

    def test_deleted_pregnancy_is_not_active(self):
        Pregnancy.objects.create(customer=self.customer, due_date=date.today())
        self.assertEqual(self.delete('pregnancy/delete/').status_code, 200)
        self.assertEqual(self.get('pregnancy/dashboard/').status_code, 404)


class AppointmentTests(ApiTestCase):

    def test_crud(self):
        res = self.post('pregnancy/appointments/', {
            'title': 'Ultrasound', 'doctor': 'Dr. Rao',
            'date': str(date.today() + timedelta(days=3)), 'time': '10:30'})
        self.assertEqual(res.status_code, 201, res.content)
        appt = dict(res.json())
        aid = appt.pop('id')

        self.assertEqual(len(self.get('pregnancy/appointments/?upcoming=true').json()), 1)
        appt.update(is_completed=True)
        res = self.put(f'pregnancy/appointments/{aid}/', appt)
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(self.get('pregnancy/appointments/?upcoming=true').json(), [])

        self.assertEqual(self.delete(f'pregnancy/appointments/{aid}/').status_code, 200)


class ChecklistTests(ApiTestCase):

    def test_defaults_toggle_add_delete(self):
        body = self.get('pregnancy/checklist/').json()
        self.assertEqual([c['id'] for c in body['categories']], ['mom', 'baby', 'other'])
        total = body['total_count']
        first = body['categories'][0]['items'][0]

        body = self.patch(f"pregnancy/checklist/items/{first['id']}/",
                          {'checked': True}).json()
        self.assertEqual(body['packed_count'], 1)

        res = self.post('pregnancy/checklist/items/', {'label': 'Slippers'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['total_count'], total + 1)
        custom = res.json()['categories'][2]['items'][-1]
        self.assertTrue(custom['is_custom'])

        # default items cannot be deleted, custom ones can
        self.assertEqual(self.delete(f"pregnancy/checklist/items/{first['id']}/").status_code, 400)
        res = self.delete(f"pregnancy/checklist/items/{custom['id']}/")
        self.assertEqual(res.json()['total_count'], total)


class ChildWeightTests(ApiTestCase):

    def test_gain_and_age_labels(self):
        self.post('pregnancy/child-weights/', {
            'entry_date': '2026-01-01', 'age_months': 6, 'weight_kg': 7.5})
        res = self.post('pregnancy/child-weights/', {
            'entry_date': '2026-04-01', 'age_months': 15, 'weight_kg': 8.9})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()['gain_kg'], 1.4)

        body = self.get('pregnancy/child-weights/').json()
        self.assertEqual([e['age_label'] for e in body], ['6 months', '1 year 3m'])
        self.assertEqual(self.delete(f"pregnancy/child-weights/{body[0]['id']}/").status_code, 200)
