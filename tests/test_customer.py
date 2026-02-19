import unittest
from application import create_app, db
from config import TestingConfig

class TestCustomers(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)

        with self.app.app_context():
            db.drop_all()
            db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        }

        response = self.client.post("/customers/", json=payload)

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["email"], "john@example.com")

    def test_create_customer_missing_email(self):
        payload = {
            "name": "no email",
            "phone": "1234567890",
            "password": "securepassword123"
        }

        response = self.client.post("/customers/", json=payload)

        self.assertEqual(response.status_code, 400)

    def test_login_customer(self):
        # create customer
        self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })

        # attempt login
        response = self.client.post("/customers/login", json={
            "email": "john@example.com",
            "password": "securepassword123"
        })

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("auth_token", data)

    def test_login_customer_invalid_password(self):
        # create customer
        self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })

        # attempt login with invalid password
        response = self.client.post("/customers/login", json={
            "email": "john@example.com",
            "password": "wrongpassword123"
        })

        self.assertEqual(response.status_code, 401)

