from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.MyCpn.Context import Context, Variable, ColorSet, Priority, Function, _get_element
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.Translator.translator_functions import *
from CpnDiscovery.Translator.basic_parts import ArcInscription

class SyncPlace:
    def __init__(self, context: Context, cpn: CPN, sync: SynchronizationRestriction):
        self.context = context
        self.cpn = cpn
        self.color_a: ColorSet = self.context.get_color(sync.type_a,by="name")
        self.color_b: ColorSet = self.context.get_color(sync.type_b,by="name")
        self.prod_color = self.context.get_prod_color(self.color_a, self.color_b)
        self.sync_place_color = self.context.get_mult_color(self.prod_color)
        self.sync_place_variable = self.context.create_new_var(self.sync_place_color)
        self.activities = sync.transitions
        self.incoming_arcs: dict[str, SyncArcInscription] = {} #key is transition id
        self.outgoing_arcs: dict[str, SyncArcInscription] = {} #key is transition id
        self.create_connections()
    
    def get_place(self, format: str = "ocpn"):
        return Place(
            name=f"p_sync_{self.color_a.name}_{self.color_b.name}",
            colorSet=self.sync_place_color,
            initialMarking="[[]]"
        )

    def create_connections(self):
        for act in self.activities:
            self.connect_activity(act)
        for color in [self.color_a, self.color_b]:
            self.add_cleanup_arcs(color.name)

    def connect_activity(self, activity: str):
        trans = self.cpn.get_transition(key=activity, by="name")
        tid = trans.id
        variable_a = self.cpn.get_variables_of_transition(self.context, trans, colorSet=self.color_a, consider="incoming")
        variable_b = self.cpn.get_variables_of_transition(self.context, trans, colorSet=self.color_b, consider="incoming")
        
        if len(variable_a) > 1 or len(variable_b) > 1:
            raise ValueError("Can't handle multiple variable per arc!")
        elif len(variable_a) == 0 or len(variable_b) == 0:
            raise ValueError("Cant handle transitions without variables!")

        variable_a = list(variable_a)[0]
        variable_b = list(variable_b)[0]

        is_a_mult = self.context.isMultColor(variable_a.colorSet)
        is_b_mult = self.context.isMultColor(variable_b.colorSet)

        self.outgoing_arcs[tid] = SyncArcInscription(
            is_incoming = False, 
            otype= self.sync_place_color.name, 
            sync_place_var = self.sync_place_variable, 
            var_a = variable_a, 
            var_b = variable_b,
            is_a_mult= is_a_mult,
            is_b_mult=is_b_mult
            )
        self.incoming_arcs[tid] = SyncArcInscription(
            is_incoming = True,
            otype= self.sync_place_color.name, 
            sync_place_var = self.sync_place_variable, 
            var_a = variable_a, 
            var_b = variable_b,
            is_a_mult= is_a_mult,
            is_b_mult=is_b_mult
            )
    
    def add_cleanup_arcs(self, otype: str):
        # find last transition of otype
        end_transitions = self.cpn.get_end_transitions_of_color(self.context.get_color(otype, by="name"), self.context)
        
        for end_transition in list(end_transitions):
            variable = self.cpn.get_variables_of_transition(self.context, end_transition, colorSet=self.context.get_color(otype,by="name"), consider="incoming")
            if len(variable) > 1:
                raise ValueError("Can't handle multiple variable per arc!")
            variable = list(variable)[0]
            is_mult = self.context.isMultColor(variable.colorSet)

            if end_transition.id in self.incoming_arcs.keys():
                #activity is used in sync set and thus only incomin arc has to be modifed
                self.incoming_arcs[end_transition.id].mark_as_cleanup(otype)

            else:
                # yet uninvolved transition
                isA = self.color_a == self.context.get_base_color_of_mult(variable.colorSet)
                self.outgoing_arcs[end_transition.id] = SyncArcInscription(
                    is_incoming = False, 
                    otype= self.sync_place_color.name, 
                    sync_place_var = self.sync_place_variable, 
                    var_a = variable if isA else None, 
                    var_b = variable if not isA else None,
                    is_a_mult= is_mult if isA else None,
                    is_b_mult=is_mult if not isA else None
                )
                
                self.incoming_arcs[end_transition.id] = SyncArcInscription(
                    is_incoming = True, 
                    otype= self.sync_place_color.name, 
                    sync_place_var = self.sync_place_variable, 
                    var_a = variable if isA else None, 
                    var_b = variable if not isA else None,
                    is_a_mult= is_mult if isA else None,
                    is_b_mult=is_mult if not isA else None
                )
                self.incoming_arcs[end_transition.id].mark_as_cleanup(variable.colorSet.name)

class SyncGuardPart:
    def __init__(self, sync_place_var: Variable, var_a: Variable, var_b: Variable, is_a_mult: bool, is_b_mult: bool, sync_type: SyncType):
        self.sync_place_var = sync_place_var
        self.var_a = var_a
        self.var_b = var_b
        self.is_a_mult = is_a_mult
        self.is_b_mult = is_b_mult
        self.sync_type = sync_type

    def create_guard_part(self, format: str = "ocpn"):
        if format == "ocpn":
            list_a, list_b = _dynamic_var_list_stringify(self.var_a, self.var_b, self.is_a_mult, self.is_b_mult)
            
            if_part = f"{Functions.exists1().name}({list_a}, {self.sync_place_var.name})"
            if self.sync_type == SyncType.SYMETRIC:
                if_part += f" || {Functions.exists2().name}({list_b}, {self.sync_place_var.name})"
            
            if_body = f"{Functions.all_pair_exists().name}({list_a}, {list_b}, {self.sync_place_var.name})"
            
            return f"{Functions.imp().name}({if_part}, {if_body})"

class SyncArcInscription(ArcInscription):
    def __init__(self, is_incoming: bool, otype: str,sync_place_var: Variable, var_a: Variable, var_b: Variable, is_a_mult: bool, is_b_mult: bool):
        super().__init__(otype,[sync_place_var, var_a, var_b])
        self.is_incoming = is_incoming # incoming towards the sync place
        self.is_clean_up_a = False
        self.is_clean_up_b = False
        self.sync_place_otype = otype
        self.sync_place_var = sync_place_var
        self.var_a = var_a
        self.var_b = var_b
        self.is_a_mult = is_a_mult
        self.is_b_mult = is_b_mult

    def mark_as_cleanup(self, otype: str):
        if self.var_a and otype == self.var_a.colorSet.name:
            self.is_clean_up_a = True
        if self.var_b and otype == self.var_b.colorSet.name:
            self.is_clean_up_b = True

    def get_arc_inscription(self, format: str = "ocpn") -> str:
        if not self.is_incoming:
            return self.get_outgoing_arc_inscription(format)

        if self.is_clean_up_a or self.is_clean_up_b:
            return self.get_cleanup_arc_inscription(format)
        else:
            return self.get_incoming_arc_inscription(format)
        
    def get_incoming_arc_inscription(self, format: str = "ocpn") -> str:
        
        if self.is_a_mult and self.is_b_mult:
            union_list = f"{Functions.get_pairs().name}({self.var_a.name}, {self.var_b.name})"
        elif self.is_a_mult:
            union_list = f"{Functions.get_pairs().name}({self.var_a.name}, [{self.var_b.name}])"
        elif self.is_b_mult:
            union_list = f"{Functions.get_pairs().name}([{self.var_a.name}], {self.var_b.name})"
        else:
            union_list = f"[[{self.var_a.name},{self.var_b.name}]]"

        return f"{Functions.union().name}({union_list},{self.sync_place_var.name})"

    def get_cleanup_arc_inscription(self, format: str = "ocpn") -> str:
        #TODO: Consider is_mult
        list_a, list_b = _dynamic_var_list_stringify(self.var_a, self.var_b, self.is_a_mult, self.is_b_mult)
        if self.is_clean_up_a and self.is_clean_up_b:
            return f"{Functions.remove1().name}({list_a},{Functions.remove2().name}({list_b},{self.sync_place_var.name}))"
        elif self.is_clean_up_a:
            return f"{Functions.remove1().name}({list_a},{self.sync_place_var.name})"
        else:
            return f"{Functions.remove2().name}({list_b},{self.sync_place_var.name})"

    def get_outgoing_arc_inscription(self, format: str = "ocpn") -> str:
        return f"{self.sync_place_var.name}"

def _dynamic_var_list_stringify(var_a: Variable, var_b: Variable, is_a_mult: bool, is_b_mult: bool) -> tuple[str, str]:
    list_a = ""
    if var_a:
        list_a = f"[{var_a.name}]"
        if is_a_mult:
            list_a = f"{var_a.name}"
    
    list_b = ""
    if var_b:
        list_b = f"[{var_b.name}]"
        if is_b_mult:
            list_b = f"{var_b.name}"
    return list_a, list_b