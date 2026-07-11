from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from roomnest.production_safety import validate_database_configuration


class ProductionSafetyTests(SimpleTestCase):
    def test_validate_database_configuration_rejects_sqlite_in_production(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_database_configuration(
                {"ENGINE": "django.db.backends.sqlite3"},
                is_production=True,
                database_url="sqlite:///db.sqlite3",
            )

    def test_validate_database_configuration_accepts_postgres_config(self):
        validated = validate_database_configuration(
            {"ENGINE": "django.db.backends.postgresql"},
            is_production=True,
            database_url="postgresql://user:pass@db.example.com:5432/roomnest",
        )
        self.assertEqual(validated["ENGINE"], "django.db.backends.postgresql")
