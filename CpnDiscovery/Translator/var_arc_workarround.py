from CpnDiscovery.MyCpn.Context import *
from CpnDiscovery.MyCpn.CPN import *


class VarArcExpander():
    def __init__(self, cpn_project: CPN_Project, format: str = "ocpn"):
        self.cpn_project = cpn_project
        self.format = format
        self.context = self.cpn_project.context
        self.place_prefix = "_var_"
        self.trans_prefix_rev = "_varR_"
        self.trans_prefix_for = "_varF_"

    def apply_var_arc_workarround(self):
        old_cpns = copy.deepcopy(self.cpn_project.cpns)
        for i,cpn in enumerate(old_cpns):
            for arc in cpn.arcs:
                # expand arcs from a place to a transition with only a single mult_var
                if isinstance(arc.source, Transition):
                    continue
                variables = self.context.parse_variable_from_text(arc.inscription)
                if len(variables)!=1:
                    continue
                if variables[0].colorSet.type != ColorSetTypes.LIST:
                    continue
                if arc.source.colorSet.type == ColorSetTypes.LIST: #if the place is of the correct type no need to replace
                    continue
                self.expand_single_arc(self.cpn_project.cpns[i],arc)

    def expand_single_arc(self, cpn: CPN, arc: Arc):
        place = arc.get_place()
        transition = arc.get_transition()
        mult_variable = self.context.parse_variable_from_text(arc.inscription)
        
        if len(mult_variable) > 1:
            raise NotImplementedError("Can't expand arcs with multiple variables in inscription")
        mult_variable = mult_variable[0]
        if not self.context.isMultColor(mult_variable.colorSet):
            raise ValueError(f"Expected ColorSet of Type List got {mult_variable.colorSet.type}")

        base_color = self.context.get_base_color_of_mult(mult_variable.colorSet)
        variable = self.context.get_variable_by_color(base_color)

        intermediate_place = Place(
            name=self.place_prefix+transition.name+"_"+variable.colorSet.name,
            colorSet=mult_variable.colorSet,
            initialMarking=[[]]
        )
        t_reverse = Transition(
            name=None,
            id=self.trans_prefix_rev+arc.id,
            priority=Priority.low(),
            guard=f"{mult_variable.name}.len() > 0"
        )
        t_forward = Transition(
            name=None,
            id=self.trans_prefix_for+arc.id,
            priority=Priority.normal()
        )
        cpn.add_place(intermediate_place)
        cpn.add_transition(t_reverse)
        cpn.add_transition(t_forward)

        # remove old arc
        cpn.arcs.remove(arc)
        # set arcs
        cpn.add_arc(
            Arc(
                id = t_forward.id+"1",
                source=place,
                target=t_forward,
                inscription=f"{variable.name}"
            )
        )
        cpn.add_arc(
            Arc(
                id = t_reverse.id+"1",
                source=t_reverse,
                target=place,
                inscription=f"{mult_variable.name}"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"1",
                source=t_forward,
                target=intermediate_place,
                inscription=f"{mult_variable.name}+[{variable.name}]"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"2",
                source=intermediate_place,
                target=t_forward,
                inscription=f"{mult_variable.name}"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"3",
                source=t_reverse,
                target=intermediate_place,
                inscription=f"[]"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"4",
                source=intermediate_place,
                target=t_reverse,
                inscription=f"{mult_variable.name}"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"5",
                source=transition,
                target=intermediate_place,
                inscription=f"[]"
            )
        )
        cpn.add_arc(
            Arc(
                id = intermediate_place.name+"6",
                source=intermediate_place,
                target=transition,
                inscription=f"{mult_variable.name}"
            )
        )

        