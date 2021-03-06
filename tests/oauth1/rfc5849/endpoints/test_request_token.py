from __future__ import unicode_literals, absolute_import

from mock import MagicMock
from ....unittest import TestCase

from oauthlib.oauth1.rfc5849 import Client
from oauthlib.oauth1 import RequestValidator
from oauthlib.oauth1.rfc5849.endpoints import RequestTokenEndpoint


class RequestTokenEndpointTest(TestCase):

    def setUp(self):
        self.validator = MagicMock(wraps=RequestValidator())
        self.validator.check_client_key.return_value = True
        self.validator.allowed_signature_methods = ['HMAC-SHA1']
        self.validator.get_client_secret.return_value = 'bar'
        self.validator.get_default_realms.return_value = ['foo']
        self.validator.timestamp_lifetime = 600
        self.validator.check_realm.return_value = True
        self.validator.validate_client_key.return_value = True
        self.validator.validate_requested_realm.return_value = True
        self.validator.validate_redirect_uri.return_value = True
        self.validator.validate_timestamp_and_nonce.return_value = True
        self.validator.dummy_client = 'dummy'
        self.validator.dummy_secret = 'dummy'
        self.validator.save_request_token = MagicMock()
        self.endpoint = RequestTokenEndpoint(self.validator)
        self.client = Client('foo', client_secret='bar', realm='foo',
                callback_uri='https://c.b/cb')
        self.uri, self.headers, self.body = self.client.sign(
                'https://i.b/request_token')

    def test_check_redirect_uri(self):
        client = Client('foo')
        uri, headers, _ = client.sign(self.uri)
        u, h, b, s = self.endpoint.create_request_token_response(
                uri, headers=headers)
        self.assertEqual(s, 400)
        self.assertIn('invalid_request', b)

    def test_check_realm(self):
        self.validator.check_realm.return_value = False
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=self.headers)
        self.assertEqual(s, 400)
        self.assertIn('invalid_request', b)

    def test_validate_client_key(self):
        self.validator.validate_client_key.return_value = False
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=self.headers)
        self.assertEqual(s, 401)

    def test_validate_realm(self):
        self.validator.validate_requested_realm.return_value = False
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=self.headers)
        self.assertEqual(s, 401)

    def test_validate_redirect_uri(self):
        self.validator.validate_redirect_uri.return_value = False
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=self.headers)
        self.assertEqual(s, 401)

    def test_validate_signature(self):
        client = Client('foo', callback_uri='https://c.b/cb')
        _, headers, _ = client.sign(self.uri + '/extra')
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=headers)
        self.assertEqual(s, 401)

    def test_valid_request(self):
        u, h, b, s = self.endpoint.create_request_token_response(
                self.uri, headers=self.headers)
        self.assertEqual(s, 200)
        self.assertIn('oauth_token', b)

    def test_uri_provided_realm(self):
        client = Client('foo', callback_uri='https://c.b/cb',
                client_secret='bar')
        uri = self.uri + '?realm=foo'
        _, headers, _ = client.sign(uri)
        u, h, b, s = self.endpoint.create_request_token_response(
                uri, headers=headers)
        self.assertEqual(s, 200)
        self.assertIn('oauth_token', b)
