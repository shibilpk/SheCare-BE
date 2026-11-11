from core.testing.api import ApiTestCase


class HealthTipTests(ApiTestCase):

    def test_seeded_tips(self):
        res = self.get('general/health-tips/')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertGreaterEqual(len(res.json()), 10)
