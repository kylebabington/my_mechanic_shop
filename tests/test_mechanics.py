import unittest

from application import create_app, db
from config import TestingConfig

class TestMechanics(unittest.TestCase):

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

    def test_create_mechanic(self):
        payload = {
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        }

        response = self.client.post("/mechanics/", json=payload)

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["email"], "bob@garage.com")

    def test_create_mechanic_duplicate_email(self):
        payload = {
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        }

        self.client.post("/mechanics/", json=payload)

        duplicate_response = self.client.post("/mechanics/", json=payload)

        self.assertEqual(duplicate_response.status_code, 400)

    def test_update_mechanic(self):
        create_response = self.client.post("/mechanics/", json={
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        })

        mechanic_id = create_response.get_json()["id"]

        update_response = self.client.put(f"/mechanics/{mechanic_id}", json={
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 55000
        })

        self.assertEqual(update_response.status_code, 200)

        updated_data = update_response.get_json()

        self.assertEqual(updated_data["salary"], 55000)

    def test_delete_mechanic(self):
        create_response = self.client.post("/mechanics/", json={
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        })

        mechanic_id = create_response.get_json()["id"]

        delete_response = self.client.delete(f"/mechanics/{mechanic_id}")

        self.assertEqual(delete_response.status_code, 204)

        get_response = self.client.get(f"/mechanics/{mechanic_id}")

        self.assertEqual(get_response.status_code, 404)

    def test_most_tickets_empty(self):
        response = self.client.get("/mechanics/most-tickets")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIsInstance(data, list)

    def test_list_mechanics(self):
        # create one mechanic so list isn't empty
        self.client.post("/mechanics/", json={
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        })

        response = self.client.get("/mechanics/")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_get_mechanic_by_id_success(self):
        # ------------------------------------------------------------
        # Create a mechanic
        # ------------------------------------------------------------
        create_response = self.client.post("/mechanics/", json={
            "name": "Bob Smith",
            "email": "bob@garage.com",
            "phone": "1234567890",
            "salary": 50000
        })
        self.assertEqual(create_response.status_code, 201)

        mechanic_id = create_response.get_json()["id"]

        # ------------------------------------------------------------
        # GET the mechanic by id
        # ------------------------------------------------------------
        get_response = self.client.get(f"/mechanics/{mechanic_id}")
        self.assertEqual(get_response.status_code, 200)

        # ------------------------------------------------------------
        # response body exists
        # ------------------------------------------------------------
        data = get_response.get_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], mechanic_id)
        self.assertEqual(data["email"], "bob@garage.com")

    def test_get_mechanic_by_id_404(self):
        # Negative: mechanic doesn't exist
        response = self.client.get("/mechanics/999999")
        self.assertEqual(response.status_code, 404)