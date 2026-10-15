from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.MyCpn.Context import Context, Variable, ColorSet, Priority, Function, _get_element
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.Translator.translator_functions import *
from CpnDiscovery.Translator.synchronization_translator import *
from CpnDiscovery.Translator.overwide_var_arc_translator import *
from CpnDiscovery.Translator.basic_parts import *
from CpnDiscovery.Translator.var_arc_workarround import VarArcExpander

class Guard:
    def __init__(self, context: Context):
        self.context = context
        self.variables: set[Variable] = set()
        self.otguardparts: dict[str, OTGuardPart] = {} # key is otype
        self.synchronizationparts: list[SyncGuardPart] = [] # each element is a synchronization restriction that can be added with AND

    def create_guard_str(self, format: str = "ocpn") -> str:
        guard_str = ""
        if format == "ocpn":
            land = "&&"
            lor = "||"
            for part in self.otguardparts.values():
                if part.create_guard_part(format) == "":
                    continue
                guard_str += f"({part.create_guard_part(format)}) {land} "
            for sync in self.synchronizationparts:
                guard_str += f"({sync.create_guard_part(format)}) {land} "

            guard_str = guard_str[:-4]
        else:
            raise NotImplementedError
        
        return guard_str
    
    def add_variable_range_restriction(self, restriction: NarrowVariableArcRestriction, variable: Variable):
        if restriction.otype in self.otguardparts.keys(): #if it is allready present just change it
            self.otguardparts[otype].set_range(restriction.range)
            return

        self.otguardparts[restriction.otype] = OTGuardPart(
            restriction.otype,
            variable,
            restriction.range,
            excludeOpt=True
        )
        self.variables.add(Variable)
    
    def add_optional_ot_restriction(self, otype: str, isOptional: bool, variable: Variable):
        if otype in self.otguardparts.keys(): #if it is allready present just change it
            self.otguardparts[otype].optional = isOptional
            self.otguardparts[otype].excludeOpt = False
            return

        self.otguardparts[otype] = OTGuardPart(
            otype,
            variable,
            optional=isOptional,
            excludeOpt=False
        )
        self.variables.add(Variable)
    
    def add_synchronization_restriction(self, restriction: SynchronizationRestriction, sync_place_var: Variable, var_a: Variable, var_b: Variable, is_a_mult: bool, is_b_mult: bool):
        self.synchronizationparts.append(
            SyncGuardPart(
                sync_place_var,
                var_a,
                var_b,
                is_a_mult,
                is_b_mult,
                restriction.sync_type
            )
        )     
        

class TransTransition:
    def __init__(self, context: Context, name: str):
        self.context = context
        self.name = name
        self.guard: Guard = Guard(self.context)
        self.incoming_arcs: dict[str, ArcInscription] = {} # str is otype
        self.outgoing_arcs: dict[str, ArcInscription] = {} # str is otype

    def get_guard(self, format: str = "ocpn"):
        return self.guard.create_guard_str(format)

    def add_narrow_variable_arcs_restriction(self, restriction: NarrowVariableArcRestriction):
        color = self.context.get_mult_color(restriction.otype)
        var = self.context.get_variable_by_color(color)
        self.guard.add_variable_range_restriction(restriction, var)
        self.incoming_arcs[restriction.otype] = ArcInscription(restriction.otype, [var])
        self.outgoing_arcs[restriction.otype] = ArcInscription(restriction.otype, [var])

    def add_optional_ot_restriction(self, otype: str, isOptional: bool):
        color = self.context.get_mult_color(otype)
        var = self.context.get_variable_by_color(color)
        self.guard.add_optional_ot_restriction(otype, isOptional, var)
        self.incoming_arcs[otype] = ArcInscription(otype, [var])
        self.outgoing_arcs[otype] = ArcInscription(otype, [var])

    def add_synchronization_restriction(self, cpn: CPN, transition: str, restriction: SynchronizationRestriction, sync_place_var: Variable):
        trans = cpn.get_transition(key=transition, by="name")
        color_a = self.context.get_color(restriction.type_a, by="name")
        color_b = self.context.get_color(restriction.type_b, by="name")
        variable_a = cpn.get_variables_of_transition(self.context, trans, colorSet=color_a, consider="incoming")
        variable_b = cpn.get_variables_of_transition(self.context, trans, colorSet=color_b, consider="incoming")
        
        if len(variable_a) > 1 or len(variable_b) > 1:
            raise ValueError("Can't handle multiple variable per arc!")
        elif len(variable_a) == 0 or len(variable_b) == 0:
            raise ValueError("Cant handle empty transitions without variables!")

        variable_a = list(variable_a)[0]
        variable_b = list(variable_b)[0]

        is_a_mult = self.context.isMultColor(variable_a.colorSet)
        is_b_mult = self.context.isMultColor(variable_b.colorSet)
        self.guard.add_synchronization_restriction(restriction, sync_place_var, variable_a, variable_b, is_a_mult, is_b_mult)




class TranslatorObject:
    def __init__(self, cpn_proj: CPN_Project):
        self.context = cpn_proj.context
        self.cpn = cpn_proj.cpns[0]
        self.transitions: dict[str, TransTransition] = {} # keys are transition names
        self.places: list[SyncPlace] = []
        self.functions: list[TFunction] = []
        # add structural change componetnts here as well

    def create_restricted_cpn(self, format: str = "ocpn"):
        for transition in self.transitions.values():
            cpn_trans = self.cpn.get_transition(transition.name, by="name")
            cpn_trans.guard = transition.get_guard()
            
            # go through the associated arcs and set variables
            incoming, outgoing = self.cpn.get_arcs_from_transition(cpn_trans)
            for arc in incoming:
                otype = arc.get_place().colorSet.name
                if otype in transition.incoming_arcs.keys():
                    arc.inscription = transition.incoming_arcs[otype].get_arc_inscription()
            for arc in outgoing:
                otype = arc.get_place().colorSet.name
                if otype in transition.outgoing_arcs.keys():
                    arc.inscription = transition.outgoing_arcs[arc.get_place().colorSet.name].get_arc_inscription()
        
        for place in self.places:
            cpn_place = place.get_place(format)
            self.cpn.add_place(cpn_place)
            for arc in place.incoming_arcs.keys():
                self.cpn.add_arc(
                    Arc( 
                        id=f"{arc}->{cpn_place.name}",
                        source=self.cpn.get_transition(arc, by="id"),
                        target=cpn_place,
                        inscription=place.incoming_arcs[arc].get_arc_inscription(format)
                    )
                )
            for arc in place.outgoing_arcs.keys():
                self.cpn.add_arc(
                    Arc(
                        id=f"{cpn_place.name}->{arc}",
                        source=cpn_place,
                        target=self.cpn.get_transition(arc, by="id"), #will cause issues with silent transition #TODO migrate to id
                        inscription=place.outgoing_arcs[arc].get_arc_inscription(format)
                    )
                )
            
            #add functions
            for func in self.functions:
                self.context.add_function(Function(func.name, func.code))


    def add_narrow_variable_arcs_restrictions(self, narrow_restrictions: list[NarrowVariableArcRestriction]):
        for narrow in narrow_restrictions:
            if narrow.otype not in [col.name for col in self.context.colorSets]:
                continue
            if narrow.transition not in self.transitions.keys():
                self.transitions[narrow.transition] = TransTransition(self.context, narrow.transition)
            self.transitions[narrow.transition].add_narrow_variable_arcs_restriction(narrow)
            
    def add_optional_ot_restrictions(self, optional_ot_restriction: list[OptionalOTRestriction]):
        optional_trans = {} # dict with keys = transition names and values = optional ots
        for optional in optional_ot_restriction:
            if optional.otype not in [col.name for col in self.context.colorSets]:
                continue
            if optional.transition not in optional_trans.keys():
                optional_trans[optional.transition] = []
            optional_trans[optional.transition].append(optional.otype)

        for trans in self.cpn.transitions:
            variables = self.cpn.get_variables_of_transition(self.context, trans)
            mult_vars = []
            for mvar in variables:
                if self.context.isMultColor(mvar.colorSet):
                    mult_vars.append(mvar)
            
            if len(mult_vars) == 0:
                continue

            # for every variable arc we add an optional_ot_restriction
            if trans.name not in self.transitions.keys():
                 self.transitions[trans.name] = TransTransition(self.context, trans.name)
            
            for v in mult_vars:
                base_color = self.context.get_base_color_of_mult(v.colorSet)
                otype = base_color.name
                if trans.name in optional_trans.keys() and otype in optional_trans[trans.name]:
                    self.transitions[trans.name].add_optional_ot_restriction(otype,True)
                else:
                    self.transitions[trans.name].add_optional_ot_restriction(otype,False)

    def add_synchronization_restrictions(self, synchronizations: list[SynchronizationRestriction]):
        # Assumes that a typextype combination might at most have one synchronization
        model_types = [col.name for col in self.context.colorSets]
        for sync in synchronizations:             
            if sync.type_a  not in model_types or sync.type_b not in model_types: #types not in the model are ignored
                continue
            sync_p = SyncPlace(
                    self.context,
                    self.cpn,
                    sync
                )
            self.places.append(sync_p)

            for trans in sync.transitions:
                if trans not in self.transitions.keys():
                    self.transitions[trans] = TransTransition(self.context, trans)
                self.transitions[trans].add_synchronization_restriction(self.cpn, trans, sync, sync_p.sync_place_variable)
            # add guard to transitions
        self.functions = Functions.get_all_functions(format="ocpn")

# adds restrictions to the CPN inplace
def add_restrictions(restrictions: RestrictionCollection, cpn_proj=CPN_Project, format: str = "ocpn", expanded_var_arcs: bool = False):
    # has to go through all restriction types and 
    translator = TranslatorObject(cpn_proj)
    if len(restrictions.narrow_var_arcs) > 0:
        translator.add_narrow_variable_arcs_restrictions(restrictions.narrow_var_arcs)
    if len(restrictions.optional_ot) > 0:
        translator.add_optional_ot_restrictions(restrictions.optional_ot)
    if len(restrictions.synchronizations)>0:
        translator.add_synchronization_restrictions(restrictions.synchronizations)
    translator.create_restricted_cpn()

    if expanded_var_arcs:
        VarArcExpander(cpn_proj,format).apply_var_arc_workarround()


if __name__ == "__main__":
    base_model_path = "tests/test_models/"
    model_name = "AB_Synchronized_CPN"
    restr_base_path = "tests/test_restriction/"
    restr_name = "AP_Synchronized_Restrictions"


    cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
    restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
    
    add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=False)
    
    cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_sync.ocpn")