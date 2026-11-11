import json

from django.test import Client, TestCase
from ninja_jwt.tokens import RefreshToken

from accounts.models import User
from customers.models import Customer


class ApiTestCase(TestCase):
    """TestCase with a logged-in customer and JSON helpers."""

    password = 'S3cure-pass!'

    def setUp(self):
        self.user = User.objects.create_user(
            username='mom@example.com', email='mom@example.com',
            password=self.password, first_name='Test', is_active=True)
        self.customer = Customer.objects.create(user=self.user)
        self.client = Client()
        self.auth = {
            'HTTP_AUTHORIZATION':
                f'Bearer {RefreshToken.for_user(self.user).access_token}'
        }

    def _call(self, method, path, data=None, auth=True):
        kwargs = dict(self.auth) if auth else {}
        if data is not None:
            kwargs['data'] = json.dumps(data, default=str)
            kwargs['content_type'] = 'application/json'
        return getattr(self.client, method)(f'/api/v1/{path}', **kwargs)

    def get(self, path, **kw):
        return self._call('get', path, **kw)

    def post(self, path, data=None, **kw):
        return self._call('post', path, data, **kw)

    def put(self, path, data=None, **kw):
        return self._call('put', path, data, **kw)

    def patch(self, path, data=None, **kw):
        return self._call('patch', path, data, **kw)

    def delete(self, path, **kw):
        return self._call('delete', path, **kw)
