import unittest
from application import create_app, db
from config import TestingConfig

class TestTickets(unittest.TestCase):

    def setUp(self):
        # create app in testing mode
        self.app = create_app(TestingConfig)

        # create database tables
        with self.app.app_context():
            db.drop_all()
            db.create_all()

        # create test client (robot postman)
        self.client = self.app.test_client()

    def tearDown(self):
        # remove session and drop all tables
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    #------------Helpers------------#

    def create_customer(self, email="john@example.com", password="securepassword123"):
        """
        Creates a customer using your real POST /customers/ endpoint.
        Returns the response JSON
        """
        response = self.client.post("/customers/", json={
            "name": "John Doe",
            "email": email,
            "phone": "1234567890",
            "password": "securepassword123"
        })
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def login_customer_get_token(self, email="john@example.com", password="securepassword123"):
        """
        Logs in using POST /customers/login.
        Returns the auth_token string.
        """
        response = self.client.post("/customers/login", json={
            "email": email,
            "password": password
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("auth_token", data)
        return data["auth_token"]

    def auth_headers(self, token):
        """
        Builds the Authorization header the same way as Postman would.
        Authorization: Bearer <token>
        """
        return {"Authorization": f"Bearer {token}"}

    def create_mechanic(self, email="bob@example.com"):
        """
        Crates a mechanic via POST /mechanics/ endpoint.
        Returns the response JSON with mechanic id
        """
        response = self.client.post("/mechanics/", json={
            "name": "Bob Smith",
            "email": email,
            "phone": "1234567890",
            "salary": 50000
        })
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_part(self, name="Oil Filter"):
        """
        Creates an inventory part via POST /inventory/.
        Returns response JSON with part id.
        """
        response = self.client.post("/inventory/", json={
            "name": name,
            "price": 12.99
        })
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    #------------Tests------------#

    def test_create_ticket_success_auth_sets_customer_id(self):
        # create + login customer
        customer = self.create_customer()
        token = self.login_customer_get_token()

        # create ticket WITHOUT customer_id (route sets from token)
        payload = {
            "VIN": "1HGBH41JXMN109186",
            "service_date": "2026-01-01",
            "service_desc": "Oil change",
        }

        response = self.client.post(
            "/service-tickets/",
            json=payload,
            headers=self.auth_headers(token)
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        # verify customer_id in returned ticket matches the logged-in customer

        self.assertEqual(data["customer_id"], customer["id"])
        self.assertEqual(data["VIN"], "1HGBH41JXMN109186")

    def test_create_ticket_without_token_fails(self):
        payload = {
            "VIN": "1HGBH41JXMN109186",
            "service_date": "2026-01-01",
            "service_desc": "Oil change",
        }

        response = self.client.post("/service-tickets/", json=payload)

        # should fail with 401 Unauthorized
        self.assertEqual(response.status_code, 401)

    def test_ticket_owner_can_get_ticket(self):
        # create first customer and login
        customer = self.create_customer(email="owner@example.com")
        token = self.login_customer_get_token(email="owner@example.com")

        # create ticket
        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "1HGBH41JXMN109186",
                "service_date": "2026-01-01",
                "service_desc": "Owner Ticket"
            },
            headers=self.auth_headers(token)
        )

        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.get_json()["id"]

        # owner fetches ticket
        get_response = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(token)
        )

        self.assertEqual(get_response.status_code, 200)

    def test_non_owner_cannot_get_ticket(self):
        # Create owner
        self.create_customer(email="owner@example.com")
        owner_token = self.login_customer_get_token(email="owner@example.com")

        # create ticket
        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "1HGBH41JXMN109186",
                "service_date": "2026-01-01",
                "service_desc": "Owner Ticket"
            },
            headers=self.auth_headers(owner_token)
        )

        ticket_id = ticket_response.get_json()["id"]

        # Create second customer
        second_customer = self.create_customer(email="intruder@example.com")
        intruder_token = self.login_customer_get_token(email="intruder@example.com")

        # intruder tries to get ticket
        get_response = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(intruder_token)
        )

        self.assertEqual(get_response.status_code, 403)

    def test_assign_mechanic_to_ticket(self):
        # Create and login customer
        self.create_customer()
        token = self.login_customer_get_token()

        # Create ticket
        ticket_res = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN123",
                "service_date": "2025-02-18",
                "service_desc": "Assignment test"
            },
            headers=self.auth_headers(token)
        )

        ticket_id = ticket_res.get_json()["id"]

        # Create mechanic
        mechanic = self.create_mechanic()
        mechanic_id = mechanic["id"]

        # Assign mechanic
        assign_res = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )

        # Verify mechanic attached
        get_res = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(token)
        )

        data = get_res.get_json()

        self.assertIn(mechanic_id, [m["id"] for m in data["mechanics"]])

    def test_remove_mechanic_from_ticket(self):
        self.create_customer()
        token = self.login_customer_get_token()

        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN123",
                "service_date": "2025-02-18",
                "service_desc": "Assignment test"
            },
            headers=self.auth_headers(token)
        )

        ticket_id = ticket_response.get_json()["id"]

        mechanic = self.create_mechanic()
        mechanic_id = mechanic["id"]

        self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )

        remove_response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}",
            headers=self.auth_headers(token)
        )

        self.assertEqual(remove_response.status_code, 200)

        get_response = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(token)
        )

        data = get_response.get_json()

        self.assertNotIn(mechanic_id, [m["id"] for m in data["mechanics"]])
    
    def test_edit_ticket_mechanics_bulk_add_remove_auth(self):
        self.create_customer()
        token = self.login_customer_get_token()

        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN-BULK-1",
                "service_date": "2025-02-18",
                "service_desc": "Bulk edit mechanics test"
            },
            headers=self.auth_headers(token)
        )

        ticket_id = ticket_response.get_json()["id"]

        # Create 3 mechanics
        m1 = self.create_mechanic(email="m1@garage.com")
        m2 = self.create_mechanic(email="m2@garage.com")
        m3 = self.create_mechanic(email="m3@garage.com")

        # First: add m1 and m2
        edit_response_1 = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [m1["id"], m2["id"]], "remove_ids": []},
            headers=self.auth_headers(token)
        )
        self.assertEqual(edit_response_1.status_code, 200)

        # Second: remove m1, add m3
        edit_response_2 = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [m3["id"]], "remove_ids": [m1["id"]]},
            headers=self.auth_headers(token)
        )
        self.assertEqual(edit_response_2.status_code, 200)

        # Verify final mechanics set by fetching ticket (owner auth)
        get_response = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(token)
        )
        self.assertEqual(get_response.status_code, 200)

        ticket = get_response.get_json()

    # If your ticket serializer includes mechanics list:
        mechanic_ids = {m["id"] for m in ticket.get("mechanics", [])}

        # Expect m2 and m3, but NOT m1
        self.assertIn(m2["id"], mechanic_ids)
        self.assertIn(m3["id"], mechanic_ids)
        self.assertNotIn(m1["id"], mechanic_ids)

    def test_add_part_to_ticket_auth(self):
        self.create_customer()
        token = self.login_customer_get_token()

        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN-PART-1",
                "service_date": "2025-02-18",
                "service_desc": "Part addition test"
            },
            headers=self.auth_headers(token)
        )
        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.get_json()["id"]

        part = self.create_part(name="Brake Pad")
        part_id = part["id"]

        add_response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}",
            headers=self.auth_headers(token)
        )
        self.assertEqual(add_response.status_code, 200)

        get_response = self.client.get(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(token)
        )
        self.assertEqual(get_response.status_code, 200)

        ticket = get_response.get_json()

        part_ids = {p["id"] for p in ticket.get("parts", [])}
        self.assertIn(part_id, part_ids)

    def test_owner_can_update_ticket(self):
        self.create_customer()
        token = self.login_customer_get_token()

        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN-UPD-1",
                "service_date": "2025-02-18",
                "service_desc": "Original"
            },
            headers=self.auth_headers(token)
        )
        ticket_id = ticket_response.get_json()["id"]

        update_response = self.client.put(
            f"/service-tickets/{ticket_id}",
            json={
                "VIN": "VIN-UPD-1",
                "service_date": "2025-02-20",
                "service_desc": "Updated description"
            },
            headers=self.auth_headers(token)
        )
        self.assertEqual(update_response.status_code, 200)

    def test_non_owner_cannot_update_ticket(self):
    # 1) Create owner
        self.create_customer(email="owner@example.com")
        owner_token = self.login_customer_get_token(email="owner@example.com")

    # 2) Owner creates ticket
        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN-AUTH-1",
                "service_date": "2025-02-18",
                "service_desc": "Owner ticket"
            },
            headers=self.auth_headers(owner_token)
        )
        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.get_json()["id"]
        # 3) Create second user (intruder)
        self.create_customer(email="intruder@example.com")
        intruder_token = self.login_customer_get_token(email="intruder@example.com")

        # 4) Intruder attempts update
        update_response = self.client.put(
            f"/service-tickets/{ticket_id}",
            json={
                "VIN": "VIN-AUTH-1",
                "service_date": "2025-02-20",
                "service_desc": "Hacked description"
            },
            headers=self.auth_headers(intruder_token)
        )
        self.assertEqual(update_response.status_code, 403)

    def test_non_owner_cannot_delete_ticket(self):
    # 1) Create owner
        self.create_customer(email="owner@example.com")
        owner_token = self.login_customer_get_token(email="owner@example.com")

    # 2) Owner creates ticket
        ticket_response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "VIN-AUTH-2",
                "service_date": "2025-02-18",
                "service_desc": "Owner ticket"
            },
            headers=self.auth_headers(owner_token)
        )

        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.get_json()["id"]

        # 3) Create intruder
        self.create_customer(email="intruder@example.com")
        intruder_token = self.login_customer_get_token(email="intruder@example.com")

        # 4) Intruder attempts delete
        delete_response = self.client.delete(
            f"/service-tickets/{ticket_id}",
            headers=self.auth_headers(intruder_token)
        )
        self.assertEqual(delete_response.status_code, 403)

    