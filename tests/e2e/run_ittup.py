# -*- coding: utf-8 -*-
"""
Runs the ittup command with the fake network: python run_ittup.py <ittup arguments>
HOME must point to a folder with the test configuration in ittup_config

The failures of the upload report are written to the JSON file in ITTUP_E2E_REPORT:
a skipped upload doesn't change the exit code
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fake_network  # noqa: E402

fake_network.install()

from ittup.core.__main__ import main  # noqa: E402
from ittup.core.report import report  # noqa: E402

sys.argv = ["ittup", *sys.argv[1:]]
try:
    main()
finally:
    if os.environ.get("ITTUP_E2E_REPORT"):
        with open(os.environ["ITTUP_E2E_REPORT"], "w", encoding="utf-8") as report_file:
            json.dump(report.failures, report_file)
