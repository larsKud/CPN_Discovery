import pm4py
from pm4py.objects.ocpn.obj import OCPetriNet
import json
from CpnDiscovery.MyCpn.CPN import *

def populate_source(_type:str, token_type: str, count: int = 6, ind: int = 0):
    if token_type == "int":
        return [i+10*ind for i in range(0,count)]
    if token_type == "string":
        prefix = _type[:1]
        return [prefix+i for i in range(0,count)]

def convert_ocpn_to_cpn(ocpn: OCPetriNet) -> CPN_Project:
    if not ocpn.name or ocpn.name == "":
        ocpn.name = "discovered_model"
    trans_prefix = "t_"
    place_prefix = "p_"
    # options are "int", "string"
    token_type = "int"
    populate_sources = True
    # get color set
    context = Context()
    color_set = set()
    for place in ocpn.places:
        color_set.add(place.object_type)

    for i, color in enumerate(color_set):
        context.add_colorSet(ColorSet(color, f"colset {color} = {token_type};", color=ColorSet.map_int_to_color(i)))

    # map places
    cpn = CPN(ocpn.name, [], [], [])
    for place in ocpn.places:
        cpn.add_place(Place(name=place.name, id=place_prefix + place.name, colorSet=context.get_color(place.object_type)))

    # map transitions
    for transition in ocpn.transitions:
        cpn.add_transition(Transition(name=transition.label, id=trans_prefix + transition.name))

    # map arcs
    for i, arc in enumerate(ocpn.arcs):
        try:
            source = cpn.get_place(place_prefix + arc.source.name)
            target = cpn.get_transition(trans_prefix + arc.target.name)
            place = source
        except ValueError:
            source = cpn.get_transition(trans_prefix + arc.source.name)
            target = cpn.get_place(place_prefix + arc.target.name)
            place = target

        is_variable = arc.is_variable
        inscription = ""
        if is_variable:
            mult_col = context.get_mult_color(place.colorSet)
            var = context.get_variable_by_color(mult_col) 
        else:
            var = context.get_variable_by_color(place.colorSet)
        
        inscription = var.name
        cpn.add_arc(Arc(id= f"{source.id}->{target.id}", source=source, target=target, inscription=inscription))
        
    if populate_sources:
        ind = 0
        for place in cpn.places:
            if "source" in place.name:
                place.initialMarking=f"{populate_source(place.colorSet.name, token_type, count=10, ind=ind)}"
                ind +=1
                
    cpn_proj = CPN_Project(
        ocpn.name+"project",
        [cpn],
        context
    )
    return cpn_proj



if __name__ == "__main__":
    db_path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order-management.sqlite"
    ocel = pm4py.read.read_ocel2(db_path)
    print("Loaded Ocel")
    ocpn: OCPetriNet = pm4py.discover_oc_petri_net(ocel)
    print("Discovered Ocpn")
    cpn_proj = convert_ocpn_to_cpn(ocpn)
    cpn_proj.export_ocpn_json("MyCpnClass\\my_models\\order_management_cpn.ocpn")
