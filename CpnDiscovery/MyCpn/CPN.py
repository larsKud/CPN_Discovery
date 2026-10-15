import copy
from typing import List, Optional, Any, Dict, Union
import json

from CpnDiscovery.MyCpn.Context import ColorSet, Context, Variable, Priority, _get_element

class Position:
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class Size:
    def __init__(self, width: float = 20, height: float = 20):
        self.width = width
        self.height = height

    def to_dict(self):
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class Place:
    def __init__(
        self,
        name: str,
        colorSet: ColorSet,
        id: str = None,
        initialMarking: str = "",
        marking: List[int] = [],
        position: Position = Position(),
        size: Size = Size(),
        colorSetOffset: Position = Position(10,10),
        tokenCountOffset: Position = Position(10, 10),
        markingOffset: Position = Position(10, 10),
    ):
        if not id:
            self.id = name
        else:
            self.id = id
        self.name = name
        self.colorSet = colorSet
        self.initialMarking = initialMarking
        self.marking = marking
        self.position = position
        self.size = size
        self.colorSetOffset = colorSetOffset
        self.tokenCountOffset = tokenCountOffset
        self.markingOffset = markingOffset

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "colorSet": self.colorSet.name,
            "initialMarking": self.initialMarking,
            "marking": self.marking,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "colorSetOffset": self.colorSetOffset.to_dict(),
            "tokenCountOffset": self.tokenCountOffset.to_dict(),
            "markingOffset": self.markingOffset.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict, context: Context):
        data["position"] = Position.from_dict(data["position"])
        data["size"] = Size.from_dict(data["size"])
        data["colorSet"] = context.get_color(data["colorSet"], by="name")
        if "colorSetOffset" in data:
            data["colorSetOffset"] = Position.from_dict(data["colorSetOffset"])
        if "tokenCountOffset" in data:
            data["tokenCountOffset"] = Position.from_dict(data["tokenCountOffset"])
        if "markingOffset" in data:
            data["markingOffset"] = Position.from_dict(data["markingOffset"])
        return cls(**data)

    def __str__(self):
        return f"[p: {self.name} | im: {self.initialMarking[0:20]}]"
    def __repr__(self):
        return str(self)

class Transition:
    def __init__(
        self,
        name: str,
        id: str = None,
        guard: str = "",
        time: str = "",
        priority: Priority = Priority.normal(),
        codeSegment: str = "",
        position: Position = Position(),
        size: Size = Size(),
    ):
        if not id:
            self.id = name
        else:
            self.id = id
        self.name = name
        self.guard = guard
        self.time = time
        self.priority = priority
        self.codeSegment = codeSegment
        self.position = position
        self.size = size
        self.is_silent = self.name == "" or self.name is None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name if isinstance(self.name, str) else "",
            "guard": self.guard,
            "time": self.time,
            "priority": self.priority.name,
            "codeSegment": self.codeSegment,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict, context: Context):
        data["position"] = Position.from_dict(data["position"])
        data["size"] = Size.from_dict(data["size"])
        try:
            data["priority"] = context.get_priority(data["priority"])
        except ValueError:
            data["priority"] = Priority.normal()
        return cls(**data)
    
    def __eq__(self, obj: "Transition"):
        return (
            self.id == obj.id and
            self.name == obj.name and
            self.guard == obj.guard and
            self.time == obj.time and
            self.priority == obj.priority
        )
    def __hash__(self):
        return hash(self.id)
    
    def __str__(self):
        return f"[t: \"{self.name}\" | guard: {self.guard != ""} ]"
    def __repr__(self):
        return str(self)

class ArcContext:
    def __init__(self, places: list[Place], transitions: list[Transition]):
        self.places = places
        self.transitions = transitions

    def get_place(self, key: str, by: str = "id") -> Place:
        for place in self.places:
            if getattr(place, by) == key:
                return place
        raise ValueError(f'No place of key "{key}"!')

    def get_transition(self, key: str, by: str = "id") -> Transition:
        for trans in self.transitions:
            if getattr(trans, by) == key:
                return trans
        raise ValueError(f'No place of key "{key}"!')


class Arc:
    def __init__(
        self,
        id: str,
        source: Union[Place, Transition],
        target: Union[Place, Transition],
        inscription: str = "",
        delay: str = "",
        isBidirectional: bool = False,
        labelOffset: Position = Position(10,10)
    ):
        self.id = id
        self.source = source
        self.target = target
        self.inscription = inscription
        self.delay = delay
        self.isBidirectional = isBidirectional
        self.labelOffset = labelOffset
    
    def get_place(self) -> Place:
        if isinstance(self.source, Place):
            return self.source
        else:
            return self.target
        
    def get_transition(self) -> Transition:
        if isinstance(self.source, Transition):
            return self.source
        else:
            return self.target

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source.id,
            "target": self.target.id,
            "inscription": self.inscription,
            "delay": self.delay,
            "isBidirectional": self.isBidirectional,
            "labelOffset": self.labelOffset.to_dict()
        }
    def __str__(self):
        return f"{self.source}->{self.target}"
    def __repr__(self):
        return str(self)
    def __eq__(self, other: Arc):
        return (
            self.id == other.id and
            self.inscription == other.inscription and
            self.source.name == other.source.name and
            self.target.name == other.target.name 
        )

    @classmethod
    def from_dict(cls, data: Dict, context: Context, arc_context: ArcContext):
        source = data["source"]
        target = data["target"]
        try:
            source = arc_context.get_place(source)
            target = arc_context.get_transition(target)
        except ValueError:
            source = arc_context.get_transition(source)
            target = arc_context.get_place(target)
        data["source"] = source
        data["target"] = target
        if "labelOffset" in data:
            data["labelOffset"] = Position.from_dict(data["labelOffset"])

        return cls(**data)


class CPN:
    def __init__(
        self,
        name: str,
        places: List[Place],
        transitions: List[Transition],
        arcs: List[Arc],
        id: str = None,
        declareConstraints: list[str] = None
    ):
        if not id:
            self.id = name
        else:
            self.id = id
        self.name = name
        self.places = places
        self.transitions = transitions
        self.arcs = arcs
        self.declareConstraints = declareConstraints if declareConstraints is not None else []

    def add_place(self, place: Place):
        self.places.append(place)

    def add_transition(self, transition: Transition):
        self.transitions.append(transition)

    def add_arc(self, arc: Arc):
        self.arcs.append(arc)

    def get_place(self, key: str, by: str = "id") -> Place:
        for place in self.places:
            if getattr(place, by) == key:
                return place
        raise ValueError(f'No place of {by} "{key}"!')

    def get_transition(self, key: str, by: str = "id") -> Transition:
        for trans in self.transitions:
            if getattr(trans, by) == key:
                return trans
        raise ValueError(f'No transition of {by} "{key}"!')

    def get_arcs_from_transition(self, key: Transition, by: str = "name") -> tuple[list[Arc], list[Arc]]:
        incoming: list[Arc] = []
        outgoing: list[Arc] = []
        for arc in self.arcs:
            if getattr(arc.get_transition(), by) == getattr(key, by):
                if isinstance(arc.source, Transition):
                    outgoing.append(arc) #if the source is the transition then the arc is outgoing for the transition
                else:
                    incoming.append(arc)
        return incoming, outgoing
    
    def get_variables_of_transition(self, context: Context, key: Transition, by: str = "id", colorSet: ColorSet = None, consider: str = "all") -> list[Variable]:
        incoming, outgoing = self.get_arcs_from_transition(key,by)
        variables: set[Variable] = set()
        arcs = []
        if consider == "incoming" or consider == "arcs" or consider == "all":
            arcs += incoming
        if consider == "outgoing" or consider == "arcs" or consider == "all":
            arcs += outgoing
        for arc in arcs:
            arc_vars = context.parse_variable_from_text(arc.inscription)
            variables = variables.union(set(arc_vars)) 
        
        # adds variables from guard
        if consider == "all":
            variables = variables.union(set(context.parse_variable_from_text(key.guard)))

        # remove sets not belonging to color if one was specified
        color_variables = set()
        if colorSet:
            for var in variables:
                color = context.get_base_color_of_mult(var.colorSet)
                if color == colorSet:
                    color_variables.add(var)
            return color_variables
        return variables


    def get_arcs_from_place(self, key: Place, by: str = "name"):
        incoming: list[Arc] = []
        outgoing: list[Arc] = []
        for arc in self.arcs:
            if getattr(arc.get_place(), by) == getattr(key, by):
                if isinstance(arc.source, Place):
                    outgoing.append(arc)
                else:
                    incoming.append(arc)
        return incoming, outgoing

    def get_outgoing_node(self, node: Transition | Place, context: Context) ->  set:
        nodes = set()
        is_place = True
        if isinstance(node, Transition):
            is_place = False

        if is_place:
            incoming, outgoing = self.get_arcs_from_place(node)
        else:
            incoming, outgoing = self.get_arcs_from_transition(node)
        return set([out.target for out in outgoing])
    
    def get_incoming_node(self, node: Transition | Place, context: Context) ->  set:
        nodes = set()
        is_place = True
        if isinstance(node, Transition):
            is_place = False

        if is_place:
            incoming, outgoing = self.get_arcs_from_place(node)
        else:
            incoming, outgoing = self.get_arcs_from_transition(node)
        return set([inc.target for inc in incoming])

    def get_subnet_of_colorSet(self, colorSet: ColorSet, context: Context) -> "CPN":
        # copy all places and arcs and transition that interact with this type NOTE does not clear guards of foreign color sets
        name = f"{self.name}_{colorSet.name}_subnet"
        subnet: CPN = CPN(
            name=name,
            places=[],
            transitions=[],
            arcs=[],
            id=name
        )
        for place in self.places:
            if place.colorSet == colorSet:         
                subnet.add_place(place)
        for arc in self.arcs:
            if arc.get_place().colorSet == colorSet:
                if isinstance(arc.target, Transition):
                    subnet.add_transition(arc.get_transition())
                subnet.add_arc(arc)
        return subnet

    def get_starting_transitions(self, context: Context) -> dict[ColorSet, list[Transition]]:
        # TODO: remove this tag if function is used
        temp = {}
        for colorSet in context.colorSets:
            temp[colorSet] = self.get_starting_transitions_of_color(context)
        return temp

    def get_starting_transitions_of_color(self, colorSet: ColorSet, context: Context, withFallback: bool = True) -> set[Transition]:
        # NOTE defines a starting place as a place without inputs
        transitions: set[Transition] = set()
        for place in self.places:
            if place.colorSet != colorSet: # early return if not the right color
                continue
            in_arcs, out_arcs = self.get_arcs_from_place(place)
            if len(in_arcs) == 0 or \
                (withFallback and (place.name.upper().__contains__('SOURCE') \
                                or place.name.upper().__contains__('START'))) \
                :
                for arc in out_arcs:
                    transitions.add(arc.target)
        return transitions
    
    def get_end_transitions_of_color(self, colorSet: ColorSet, context: Context, withFallback: bool = True) -> set[Transition]:
        # NOTE defines an end place as a place without outputs
        transitions: set[Transition] = set()
        for place in self.places:
            if place.colorSet != colorSet: # early return if not the right color
                continue
            in_arcs, out_arcs = self.get_arcs_from_place(place)
            if len(out_arcs) == 0 or \
                (withFallback and (place.name.upper().__contains__('SINK') \
                                or place.name.upper().__contains__('END'))) \
                :
                for arc in in_arcs:
                    transitions.add(arc.source)
        return transitions

    def get_visible_starting_transitions_of_color(self, colorSet: ColorSet, context: Context) -> set[Transition]:
        transitions: set[Transition] = self.get_starting_transitions_of_color(colorSet, context)
        return self.get_first_visible_transitions(set([colorSet]), context, transitions, checkForward=True)
    
    def get_visible_end_transitions_of_color(self, colorSet: ColorSet, context: Context) -> set[Transition]:
        transitions: set[Transition] = self.get_starting_transitions_of_color(colorSet, context)
        return self.get_first_visible_transitions(set([colorSet]), context, transitions, checkForward=True)
    
    def get_first_visible_transitions(self, colorSets: set[ColorSet], context: Context, transitions: set[Transition], checkForward: bool = True) -> set[Transition]:      
        _transitions = copy.deepcopy(transitions)
        # for each transition if it is silent, expand to following transitions
        new_trans = set()
        removed_trans = set([None])
        viewed_silent = set()
        while len(removed_trans) != 0:
            new_trans = set()
            removed_trans = set()
            for trans in _transitions:
                if trans.is_silent:
                    ina, outa = self.get_arcs_from_transition(key=trans, by="id")
                    if checkForward: 
                        arcs = outa
                        attr = 'target'
                    else: 
                        arcs = ina
                        attr = 'source'

                    for arc in arcs:
                        place = getattr(arc, attr)
                        if place.colorSet not in colorSets:
                            continue
                        # get out arcs and get transition add those to starting transition -> repeat till no more silent
                        pin, pout = self.get_arcs_from_place(place, by="id")
                        if checkForward: 
                            arcs2 = pin
                        else: 
                            arcs2 = pout
                        for arc2 in pout:
                            if getattr(arc2, attr) in viewed_silent:
                                continue
                            new_trans.add(getattr(arc2, attr))
                    removed_trans.add(trans)
                    viewed_silent.add(trans)
            
            _transitions.difference_update(removed_trans)
            _transitions = _transitions.union(new_trans)
        return _transitions

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "places": [p.to_dict() for p in self.places],
            "transitions": [t.to_dict() for t in self.transitions],
            "arcs": [a.to_dict() for a in self.arcs],
            "declareConstraints": self.declareConstraints
        }

    @classmethod
    def from_dict(cls, data: Dict, context: Context):
        data["places"] = [Place.from_dict(p, context) for p in data["places"]]
        data["transitions"] = [
            Transition.from_dict(t, context) for t in data["transitions"]
        ]
        arc_context = ArcContext(data["places"], data["transitions"])
        data["arcs"] = [Arc.from_dict(a, context, arc_context) for a in data["arcs"]]
        return cls(**data)


class SimulationSettings:
    def __init__(
        self,
        stepsPerRun: int = 50,
        animationDelayMs: int = 500,
        simulationEpoch: Optional[Any] = None,
        endTimeMs: Optional[Any] = None,
        keepAwakeWhileRunning: Optional[bool] = True

    ):
        self.stepsPerRun = stepsPerRun
        self.animationDelayMs = animationDelayMs
        self.simulationEpoch = simulationEpoch
        self.endTimeMs = endTimeMs
        self.keepAwakeWhileRunning = keepAwakeWhileRunning

    def to_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class CPN_Project:
    def __init__(
        self,
        ocpnName: str,
        cpns: List[CPN],
        context: Context,
        simulationSettings: SimulationSettings = SimulationSettings(),
    ):
        self.ocpnName = ocpnName
        self.cpns = cpns
        self.context = context
        self.simulationSettings = simulationSettings

    def to_dict(self):
        return {
            "ocpnName": self.ocpnName,
            "petriNets": [c.to_dict() for c in self.cpns],  # Maps back to original key
            "colorSets": [cs.to_dict() for cs in self.context.colorSets],
            "variables": [v.to_dict() for v in self.context.variables],
            "priorities": [p.to_dict() for p in self.context.priorities],
            "functions": [f.to_dict() for f in self.context.functions],
            "uses": self.context.uses,
            "values": self.context.values,
            "fusionSets": self.context.fusionSets,
            "simulationSettings": self.simulationSettings.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict):
        # Note: Handling the 'petriNets' key mapping
        cpns_data = data.pop("petriNets", [])
        context = Context.from_dict(data)
        instance = cls(
            ocpnName=data.get("ocpnName", ""),
            cpns=[CPN.from_dict(net, context) for net in cpns_data],
            context=context,
            simulationSettings=SimulationSettings.from_dict(
                data.get("simulationSettings", {})
            ),
        )
        return instance

    @staticmethod
    def import_ocpn_json(path: str) -> "CPN_Project":
        with open(path) as f:
            data = json.load(f)

        # Convert to Python Object
        return CPN_Project.from_dict(data)

    @staticmethod
    def init_empty() -> "CPN_Project":
        path = "MyCpnClass\\my_models\\EmptyCPN.ocpn"
        with open(path) as f:
            data = json.load(f)

        # Convert to Python Object
        return CPN_Project.from_dict(data)

    def export_ocpn_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)


if __name__ == "__main__":

    def test1():
        import json

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
    
    def test2():
        path = "models\\[delete]order_management.ocpn"
        with open(path) as f:
            data = json.load(f)

        # Convert to Python Object
        project = CPN_Project.from_dict(data)

        colorSet = project.context.get_color("products")
        cpn = project.cpns[0]
        subnet = cpn.get_subnet_of_colorSet(colorSet, project.context)
        project.cpns.append(subnet)

        # get s
        starting_transitions = subnet.get_visible_starting_transitions_of_color(colorSet, project.context)
        print("Starting\n", starting_transitions)
        #end_transitions = subnet.get_end_transitions_of_color(colorSet, project.context)
        #print("Ending\n", end_transitions)

        with open("models\\[delete]order_management_121fa.ocpn", "w") as f:
            json.dump(project.to_dict(), f, indent=4)
    
    # run whatever
    test2()
