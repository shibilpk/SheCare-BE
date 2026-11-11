from accounts.models import User, UserOtp
from core.testing.api import ApiTestCase


class OTPLoginTests(ApiTestCase):

    def test_send_otp_then_login(self):
        res = self.post('auth/send-otp/', {'email': 'mom@example.com'}, auth=False)
        self.assertEqual(res.status_code, 200, res.content)
        otp = UserOtp.objects.get(email='mom@example.com', is_active=True).otp

        res = self.post('auth/login-otp/',
                        {'email': 'mom@example.com', 'otp': otp}, auth=False)
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn('access', res.json())

    def test_send_otp_unknown_email(self):
        res = self.post('auth/send-otp/', {'email': 'x@example.com'}, auth=False)
        self.assertEqual(res.status_code, 404)

    def test_wrong_otp(self):
        self.post('auth/send-otp/', {'email': 'mom@example.com'}, auth=False)
        res = self.post('auth/login-otp/',
                        {'email': 'mom@example.com', 'otp': '000000x'[:6]},
                        auth=False)
        self.assertEqual(res.status_code, 400)


class AccountTests(ApiTestCase):

    def test_change_password(self):
        res = self.post('auth/change-password/', {
            'current_password': self.password,
            'new_password': 'An0ther-good-pass'})
        self.assertEqual(res.status_code, 200, res.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('An0ther-good-pass'))

    def test_change_password_wrong_current(self):
        res = self.post('auth/change-password/', {
            'current_password': 'nope', 'new_password': 'An0ther-good-pass'})
        self.assertEqual(res.status_code, 400)

    def test_deactivate_and_restore_on_login(self):
        res = self.post('auth/deactivate-account/')
        self.assertEqual(res.status_code, 200, res.content)
        self.customer.refresh_from_db()
        self.assertIsNotNone(self.customer.deactivated_at)

        res = self.post('auth/login/', {
            'email': 'mom@example.com', 'password': self.password}, auth=False)
        self.assertEqual(res.status_code, 200, res.content)
        self.customer.refresh_from_db()
        self.assertIsNone(self.customer.deactivated_at)

    def test_delete_account(self):
        res = self.delete('auth/delete-account/')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertFalse(User.objects.filter(email='mom@example.com').exists())
