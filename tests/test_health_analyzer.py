import unittest

from src.health_analyzer import assess_health, format_bytes


class TestAssessHealth(unittest.TestCase):

    def test_healthy_system(self):
        memory = {"usage_percent": 35.0}
        disk = {"usage_percent": 20.0}
        services = {"available": True, "services": []}

        findings = assess_health(memory, disk, services)

        self.assertEqual(findings[0]["severity"], "OK")

    def test_disk_warning(self):
        memory = {"usage_percent": 40.0}
        disk = {"usage_percent": 85.0}
        services = {"available": True, "services": []}

        findings = assess_health(memory, disk, services)

        self.assertEqual(findings[0]["severity"], "WARNING")
        self.assertIn("Root filesystem usage", findings[0]["issue"])

    def test_disk_critical(self):
        memory = {"usage_percent": 40.0}
        disk = {"usage_percent": 95.0}
        services = {"available": True, "services": []}

        findings = assess_health(memory, disk, services)

        self.assertEqual(findings[0]["severity"], "CRITICAL")

    def test_memory_warning(self):
        memory = {"usage_percent": 85.0}
        disk = {"usage_percent": 40.0}
        services = {"available": True, "services": []}

        findings = assess_health(memory, disk, services)

        self.assertEqual(findings[0]["severity"], "WARNING")
        self.assertIn("Memory usage", findings[0]["issue"])

    def test_failed_services(self):
        memory = {"usage_percent": 40.0}
        disk = {"usage_percent": 40.0}
        services = {
            "available": True,
            "services": ["example.service"],
        }

        findings = assess_health(memory, disk, services)

        self.assertEqual(findings[0]["severity"], "WARNING")
        self.assertIn("failed system service", findings[0]["issue"])

    def test_format_bytes(self):
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1048576), "1.0 MB")
        self.assertEqual(format_bytes(0), "0.0 B")


if __name__ == "__main__":
    unittest.main()
