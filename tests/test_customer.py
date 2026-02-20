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

    def test_get_customers_default_pagination(self):
        # create couple customers so list isn't empty
        self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })

        self.client.post("/customers/", json= {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "0987654321",
            "password": "securepassword123"
        })

        response = self.client.get("/customers/")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("customers", data)
        self.assertIsInstance(data["customers"], list)
        self.assertGreaterEqual(len(data["customers"]), 2)

    def test_get_customer_by_id_success_and_404(self):
        # create customer
        create_response = self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })
        self.assertEqual(create_response.status_code, 201)
        customer_id = create_response.get_json()["id"]

        # success
        response = self.client.get(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], customer_id)

        # negative not found
        missing = self.client.get("/customers/999999")
        self.assertEqual(missing.status_code, 404)

    def test_my_tickets_requires_auth(self):
        response = self.client.get("/customers/my-tickets")
        self.assertEqual(response.status_code, 401)

    def test_my_tickets_only_returns_my_tickets(self):
        # ------------------------------------------------------------
        # Customer 1: create + login
        # ------------------------------------------------------------
        create_1 = self.client.post("/customers/", json={
            "name": "Customer One",
            "email": "one@example.com",
            "phone": "1111111111",
            "password": "securepassword123"
        })
        self.assertEqual(create_1.status_code, 201)
        customer_1_id = create_1.get_json()["id"]

        login_1 = self.client.post("/customers/login", json={
            "email": "one@example.com",
            "password": "securepassword123"
        })
        self.assertEqual(login_1.status_code, 200)
        token_1 = login_1.get_json()["auth_token"]

        # create ticket for customer 1
        ticket_1 = self.client.post("/service-tickets/", json={
            "VIN": "1HGCM82633A004352",
            "service_date": "2025-02-18",
            "service_desc": "Customer One Ticket"
        }, headers={"Authorization": f"Bearer {token_1}"})
        self.assertEqual(ticket_1.status_code, 201)

        # ------------------------------------------------------------
        # Customer 2: create + login
        # ------------------------------------------------------------
        create_2 = self.client.post("/customers/", json={
            "name": "Customer Two",
            "email": "two@example.com",
            "phone": "2222222222",
            "password": "securepassword123"
        })
        self.assertEqual(create_2.status_code, 201)

        login_2 = self.client.post("/customers/login", json={
            "email": "two@example.com",
            "password": "securepassword123"
        })
        self.assertEqual(login_2.status_code, 200)
        token_2 = login_2.get_json()["auth_token"]

        # create ticket for customer 2
        ticket_2 = self.client.post("/service-tickets/", json={
            "VIN": "1HGCM82633A004352",
            "service_date": "2025-02-18",
            "service_desc": "Customer Two Ticket"
        }, headers={"Authorization": f"Bearer {token_2}"})
        self.assertEqual(ticket_2.status_code, 201)

        #-----------------------------------------------------------
        # Customer 1 requests my tickets
        #-----------------------------------------------------------
        my_tickets_response = self.client.get("/customers/my-tickets", headers={
            "Authorization": f"Bearer {token_1}"
            })
        self.assertEqual(my_tickets_response.status_code, 200)

        tickets = my_tickets_response.get_json()
        self.assertIsInstance(tickets, list)
        self.assertEqual(len(tickets), 1)

        # every ticket returned must belong to customer 1
        for t in tickets:
            self.assertEqual(t["customer_id"], customer_1_id)

    def test_update_me_requires_auth_and_then_succeeds(self):
        #create customer
        self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })

        # login
        login_response = self.client.post("/customers/login", json={
            "email": "john@example.com",
            "password": "securepassword123"
        })
        token = login_response.get_json()["auth_token"]

        update_payload = {
            "name": "updated name",
            "email": "updated@example.com",
            "phone": "9999999999",
            "password": "securepassword123"
        }

        # negative: no auth
        no_auth = self.client.put("/customers/me", json=update_payload)
        self.assertEqual(no_auth.status_code, 401)

        # success with auth
        response = self.client.put("/customers/me", json=update_payload, headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "updated name")
        self.assertEqual(response.get_json()["email"], "updated@example.com")
        self.assertEqual(response.get_json()["phone"], "9999999999")

    def test_delete_me_requires_auth_and_then_deletes(self):
        #create customer
        create_response = self.client.post("/customers/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "securepassword123"
        })
        self.assertEqual(create_response.status_code, 201)
        customer_id = create_response.get_json()["id"]

        # login
        login_response = self.client.post("/customers/login", json={
            "email": "john@example.com",
            "password": "securepassword123"
        })
        token = login_response.get_json()["auth_token"]

        # negative: no auth
        no_auth = self.client.delete("/customers/me")
        self.assertEqual(no_auth.status_code, 401)

        # success with auth
        delete_response = self.client.delete("/customers/me", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(delete_response.status_code, 204)

        # confirm customer is gone
        get_deleted = self.client.get(f"/customers/{customer_id}")
        self.assertEqual(get_deleted.status_code, 404)