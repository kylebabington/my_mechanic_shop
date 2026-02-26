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

    def create_ticket(self, customer_id, VIN="1HGBH41JXMN109186", service_date="2026-01-01", service_desc="Oil change"):
        """
        Creates a service ticket via POST /service-tickets/ (no auth).
        Body must include customer_id. Returns response JSON with ticket id.
        """
        response = self.client.post("/service-tickets/", json={
            "VIN": VIN,
            "service_date": service_date,
            "service_desc": service_desc,
            "customer_id": customer_id,
        })
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    #------------Tests------------#

    def test_create_ticket_success_requires_customer_id(self):
        # create customer (no login needed for shop creating ticket)
        customer = self.create_customer()

        # create ticket WITH customer_id in body (no auth)
        response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "1HGBH41JXMN109186",
                "service_date": "2026-01-01",
                "service_desc": "Oil change",
                "customer_id": customer["id"],
            }
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["customer_id"], customer["id"])
        self.assertEqual(data["VIN"], "1HGBH41JXMN109186")

    def test_create_ticket_without_customer_id_fails(self):
        payload = {
            "VIN": "1HGBH41JXMN109186",
            "service_date": "2026-01-01",
            "service_desc": "Oil change",
        }
        response = self.client.post("/service-tickets/", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_anyone_can_get_ticket_by_id(self):
        customer = self.create_customer(email="owner@example.com")
        ticket = self.create_ticket(customer["id"], service_desc="Owner Ticket")
        ticket_id = ticket["id"]

        # get ticket without auth (shop or anyone can view)
        get_response = self.client.get(f"/service-tickets/{ticket_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()["id"], ticket_id)

    def test_assign_mechanic_to_ticket(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], VIN="VIN123", service_desc="Assignment test")
        ticket_id = ticket["id"]

        mechanic = self.create_mechanic()
        mechanic_id = mechanic["id"]

        assign_res = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )
        self.assertEqual(assign_res.status_code, 200)

        get_res = self.client.get(f"/service-tickets/{ticket_id}")
        data = get_res.get_json()
        self.assertIn(mechanic_id, [m["id"] for m in data["mechanics"]])

    def test_remove_mechanic_from_ticket(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], VIN="VIN123", service_desc="Assignment test")
        ticket_id = ticket["id"]

        mechanic = self.create_mechanic()
        mechanic_id = mechanic["id"]

        self.client.put(f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}")

        remove_response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}"
        )
        self.assertEqual(remove_response.status_code, 200)

        get_response = self.client.get(f"/service-tickets/{ticket_id}")
        data = get_response.get_json()
        self.assertNotIn(mechanic_id, [m["id"] for m in data["mechanics"]])
    
    def test_edit_ticket_mechanics_bulk_add_remove(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], VIN="VIN-BULK-1", service_desc="Bulk edit mechanics test")
        ticket_id = ticket["id"]

        m1 = self.create_mechanic(email="m1@garage.com")
        m2 = self.create_mechanic(email="m2@garage.com")
        m3 = self.create_mechanic(email="m3@garage.com")

        edit_response_1 = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [m1["id"], m2["id"]], "remove_ids": []},
        )
        self.assertEqual(edit_response_1.status_code, 200)

        edit_response_2 = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [m3["id"]], "remove_ids": [m1["id"]]},
        )
        self.assertEqual(edit_response_2.status_code, 200)

        get_response = self.client.get(f"/service-tickets/{ticket_id}")
        self.assertEqual(get_response.status_code, 200)
        ticket = get_response.get_json()
        mechanic_ids = {m["id"] for m in ticket.get("mechanics", [])}
        self.assertIn(m2["id"], mechanic_ids)
        self.assertIn(m3["id"], mechanic_ids)
        self.assertNotIn(m1["id"], mechanic_ids)

    def test_add_part_to_ticket(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], VIN="VIN-PART-1", service_desc="Part addition test")
        ticket_id = ticket["id"]

        part = self.create_part(name="Brake Pad")
        part_id = part["id"]

        add_response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}"
        )
        self.assertEqual(add_response.status_code, 200)

        get_response = self.client.get(f"/service-tickets/{ticket_id}")
        self.assertEqual(get_response.status_code, 200)
        ticket = get_response.get_json()
        part_ids = {p["id"] for p in ticket.get("parts", [])}
        self.assertIn(part_id, part_ids)

    def test_update_ticket(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], VIN="VIN-UPD-1", service_desc="Original")
        ticket_id = ticket["id"]

        update_response = self.client.put(
            f"/service-tickets/{ticket_id}",
            json={
                "VIN": "VIN-UPD-1",
                "service_date": "2025-02-20",
                "service_desc": "Updated description"
            },
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["service_desc"], "Updated description")

    def test_list_tickets(self):
        customer = self.create_customer()
        self.create_ticket(customer["id"], service_desc="List tickets test")

        response = self.client.get("/service-tickets/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_delete_ticket(self):
        customer = self.create_customer()
        ticket = self.create_ticket(customer["id"], service_desc="Owner ticket")
        ticket_id = ticket["id"]

        delete_response = self.client.delete(f"/service-tickets/{ticket_id}")
        self.assertIn(delete_response.status_code, [200, 204])

        get_response = self.client.get(f"/service-tickets/{ticket_id}")
        self.assertEqual(get_response.status_code, 404)
