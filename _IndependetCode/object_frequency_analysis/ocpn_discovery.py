import pm4py
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn

# 1. Read the OCEL SQLite database (OCEL 2.0 format)
basepath = "/run/media/user/FA7F-F7F4/_MA/Data/"
ocel_path = ["container_logistics.sqlite", "order-management_shortend.sqlite", "order-management_lessAct.sqlite", "age_of_empires_ocel2.sqlite"]
for path in ocel_path:
    ocel_file = path
    ocel = pm4py.read_ocel2_sqlite(f"{basepath}{ocel_file}")

    # 2. Discover the Object-Centric Petri Net (OCPN)
    ocpn = pm4py.discover_oc_petri_net(ocel)

    # 3. Save the discovered OCPN visualization to a file (.png, .pdf, or .svg)
    output_path = f"{basepath}/OCPNS/{ocel_file.split(".sql")[0]}.ocpn"
    cpn_p = convert_ocpn_to_cpn(ocpn)
    cpn_p.export_ocpn_json(output_path)


    print(f"OCPN successfully saved to {output_path}")