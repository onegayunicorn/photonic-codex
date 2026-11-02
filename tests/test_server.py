import unittest

import server


class PhotonicCodexApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def test_health_is_versioned_and_read_only(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["service"], "photonic-codex")
        self.assertEqual(body["api_version"], "v1")
        self.assertEqual(body["mode"], "read-only-development")

    def test_module_registry_has_explicit_maturity(self):
        response = self.client.get("/api/v1/modules")
        self.assertEqual(response.status_code, 200)
        modules = response.get_json()["modules"]
        self.assertTrue(modules)
        self.assertTrue(all("status" in module and "mode" in module for module in modules))

    def test_events_limit_is_validated(self):
        self.assertEqual(self.client.get("/api/v1/events?limit=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/events?limit=0").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/events?limit=201").status_code, 400)

    def test_events_endpoint_discloses_non_durable_retention(self):
        response = self.client.get("/api/v1/events?limit=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["retention"], "process-memory")
        self.assertFalse(response.get_json()["durable"])

    def test_dashboard_is_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Photonic", response.data)

    def test_unknown_route_returns_json(self):
        response = self.client.get("/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
