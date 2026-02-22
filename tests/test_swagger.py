"""
Validate application/static/swagger.yaml against OpenAPI/Swagger 2.0 schema.
Run with: python -m unittest discover -s tests -p test_swagger.py -v
Or as part of full test suite to catch spec drift early.
"""
import os
import unittest


class TestSwaggerSpec(unittest.TestCase):
    """Schema and lint checks for application/static/swagger.yaml."""

    def test_swagger_yaml_valid(self):
        """Swagger spec must be valid OpenAPI 2.0 and load without error."""
        try:
            from openapi_spec_validator import validate_spec
            from openapi_spec_validator.readers import read_from_filename
        except ImportError:
            self.skipTest("openapi-spec-validator not installed")

        spec_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "application",
            "static",
            "swagger.yaml",
        )
        spec_path = os.path.abspath(spec_path)
        self.assertTrue(os.path.isfile(spec_path), f"Spec file not found: {spec_path}")

        spec_dict, _ = read_from_filename(spec_path)
        validate_spec(spec_dict)

    def test_swagger_expected_definitions(self):
        """Spec must define key response types used by the API."""
        try:
            from openapi_spec_validator.readers import read_from_filename
        except ImportError:
            self.skipTest("openapi-spec-validator not installed")

        spec_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "application",
            "static",
            "swagger.yaml",
        )
        spec_path = os.path.abspath(spec_path)
        spec_dict, _ = read_from_filename(spec_path)

        definitions = spec_dict.get("definitions", {})
        self.assertIn("CustomerResponse", definitions)
        self.assertIn("CustomersListResponse", definitions)
        self.assertIn("TicketResponse", definitions)
        self.assertIn("ErrorMessage", definitions)

        # Customers list must use 'count' to match implementation
        list_def = definitions.get("CustomersListResponse", {})
        props = list_def.get("properties", {})
        self.assertIn("count", props, "CustomersListResponse must have 'count' to match API")
        self.assertNotIn("total", props, "Use 'count' not 'total' for customers list")
