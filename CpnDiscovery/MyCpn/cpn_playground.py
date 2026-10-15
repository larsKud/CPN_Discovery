from CpnDiscovery.MyCpn.CPN import *

def create_simple_cpn():
    project: CPN_Project = CPN_Project.import_ocpn_json("MyCpnClass\\my_models\\EmptyCPN.ocpn")
    cpn: CPN = project.cpns[0]
    p1 = Place("Item 1", "INT")
    p2 = Place("Item 2", "INT")
    t1 = Transition("A")
    p1_to_t1 = Arc("p1_to_t1", "Item 1", "A")
    t1_to_p2 = Arc("t1_to_p2", "A", "Item 2")

    cpn.add_place(p1)
    cpn.add_place(p2)
    cpn.add_transition(t1)
    cpn.add_arc(p1_to_t1)
    cpn.add_arc(t1_to_p2)

    project.export_ocpn_json("MyCpnClass\\my_models\\SimpleCPN.ocpn")

if __name__ == "__main__":
    create_simple_cpn()
