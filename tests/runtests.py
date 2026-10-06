import os
import sys

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.test.runner import DiscoverRunner

def run_tests():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))

if __name__ == "__main__":
    run_tests()

