import pytest
import json
from CpnDiscovery.MyCpn.CPN import *

class TestCPN:
    def test_load_and_save_project(self):
        path = "tests/test_models/Demo_OCPN.ocpn"
        with open(path) as f:
            data = json.load(f)

        # Convert to Python Object
        project = CPN_Project.from_dict(data)

        # Access data
        print(project.ocpnName)
        project.cpns[0].transitions[0].name = "renamed"

        with open("models/[delete]my_cpn_export_test.ocpn", "w") as f:
            json.dump(project.to_dict(), f, indent=4)