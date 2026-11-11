from datetime import date, timedelta

from core.testing.api import ApiTestCase
from customers.models import WeightEntry


class WeightHistoryTests(ApiTestCase):

    def test_list_normalises_units_and_deletes(self):
        today = date.today()
        WeightEntry.objects.create(customer=self.customer, weight=150,
                                   unit='lb', entry_date=today - timedelta(days=30))
        WeightEntry.objects.create(customer=self.customer, weight=66,
                                   unit='kg', entry_date=today)
        WeightEntry.objects.create(customer=self.customer, weight=80,
                                   unit='kg', entry_date=today - timedelta(days=400))

        body = self.get('customer/weight-entries/?months=6').json()
        self.assertEqual([e['weight_kg'] for e in body], [68.04, 66.0])

        res = self.delete(f"customer/weight-entries/{body[0]['id']}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self.get('customer/weight-entries/').json()), 1)
