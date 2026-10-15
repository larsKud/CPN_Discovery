import json

from CpnDiscovery.MyCpn.CPN import *

path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Assets\\Demo_OCPN.ocpn"
with open(path) as f:
    data = json.load(f)

# Convert to Python Object
project = CPN_Project.from_dict(data)

# Access data
print(project.ocpnName)
project.cpns[0].transitions[0].name = "renamed"

with open("MyCpnClass\\my_models\\my_cpn_export_test.ocpn", "w") as f:
    json.dump(project.to_dict(), f, indent=4)