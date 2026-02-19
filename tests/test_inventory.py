import unittest

from application import create_app, db
from config import TestingConfig


class TestInventory(unittest.TestCase):

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

    def create_part(self, name="Oil Filter", price=12.99):
        res = self.client.post("/inventory/", json={"name": name, "price": price})
        self.assertEqual(res.status_code, 201)
        return res.get_json()

    def test_create_part_success(self):
        part = self.create_part()
        self.assertEqual(part["name"], "Oil Filter")

    def test_create_part_duplicate_name_fails(self):
        self.create_part(name="Oil Filter")
        res = self.client.post("/inventory/", json={"name": "Oil Filter", "price": 9.99})
        self.assertEqual(res.status_code, 400)

    def test_list_parts(self):
        self.create_part(name="Oil Filter")
        self.create_part(name="Brake Pad")

        res = self.client.get("/inventory/")
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

    def test_get_part_by_id(self):
        part = self.create_part(name="Air Filter")
        res = self.client.get(f"/inventory/{part['id']}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["name"], "Air Filter")

    def test_update_part(self):
        part = self.create_part(name="Basic Filter", price=10.00)
        res = self.client.put(f"/inventory/{part['id']}", json={"name": "Premium Filter", "price": 18.99})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["name"], "Premium Filter")

    def test_delete_part(self):
        part = self.create_part(name="Delete Me")
        res = self.client.delete(f"/inventory/{part['id']}")
        self.assertEqual(res.status_code, 200)

        # confirm gone
        get_res = self.client.get(f"/inventory/{part['id']}")
        self.assertEqual(get_res.status_code, 404)
