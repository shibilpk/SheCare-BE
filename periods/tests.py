from datetime import datetime

from core.testing.api import ApiTestCase
from periods.models import Period


class PeriodEditDeleteTests(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.p1 = Period.objects.create(
            customer=self.customer,
            start_date=datetime(2026, 1, 1), end_date=datetime(2026, 1, 5))
        self.p2 = Period.objects.create(
            customer=self.customer,
            start_date=datetime(2026, 1, 29), end_date=datetime(2026, 2, 2))

    def test_update(self):
        res = self.put(f'period/{self.p1.id}/', {
            'start_date': '2026-01-02', 'end_date': '2026-01-06'})
        self.assertEqual(res.status_code, 200, res.content)
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertEqual(self.p1.period_length, 5)
        self.assertEqual(self.p2.cycle_length, 27)

    def test_update_rejects_overlap(self):
        res = self.put(f'period/{self.p1.id}/', {
            'start_date': '2026-01-01', 'end_date': '2026-01-30'})
        self.assertEqual(res.status_code, 400)

    def test_delete(self):
        res = self.delete(f'period/{self.p1.id}/')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertFalse(Period.objects.filter(id=self.p1.id).exists())
        self.p2.refresh_from_db()
        self.assertIsNone(self.p2.cycle_length)
