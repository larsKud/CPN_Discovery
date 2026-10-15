from typing import List, Optional, Any, Dict, Union
from enum import Enum
from operator import attrgetter

def _get_element(list: list, key: str, by: str = "id") -> Any:
    for el in list:
        if getattr(el, by) == key:
            return el
    raise ValueError(f'No element of {by} "{key}"!')

class ColorSetTypes(Enum):
    BASIC = "basic"
    LIST = "list"
    PRODUCT = "product"


class ColorSet:
    def __init__(
        self,
        name: str,
        definition: str,
        id: str = None,
        type: ColorSetTypes = ColorSetTypes.BASIC,
        color: str = "#3b82f6",
        timed: bool = False
    ):

        self.name = name
        if not id:
            self.id = name
        else:
            self.id = id
        self.type = type
        self.definition = definition
        self.color = color
        self.timed = timed

    def to_dict(self):
        return {
            "name": self.name,
            "definition": self.definition,
            "id": self.id,
            "type": self.type.value,
            "color": self.color,
            "timed": self.timed
        }

    @classmethod
    def from_dict(cls, data: Dict):
        data['type'] = ColorSetTypes(data['type'])
        return cls(**data)

    @staticmethod
    def map_int_to_color(i: int) -> str:
        ibm_colors = [
            "#8a3ffc",  # Purple 60
            "#33b1ff",  # Cyan 40
            "#007d79",  # Teal 70
            "#ff7eb6",  # Magenta 40
            "#fa4d56",  # Red 50
            "#fff1f1",  # Red 10
            "#6fdc8c",  # Green 30
            "#4589ff",  # Blue 50
            "#d12771",  # Magenta 70
            "#d2a106",  # Yellow 40
            "#08bdba",  # Teal 40
            "#bae6ff",  # Cyan 20
            "#ba4e00",  # Orange 60
            "#d4bbff",  # Purple 20
            "#24a148",  # Green 60
            "#002d9c",  # Blue 80
            "#ee5396",  # Magenta 50
            "#009d9a",  # Teal 50
            "#001141",  # Blue 100
            "#005d5d",  # Teal 80
        ]
        return ibm_colors[i % len(ibm_colors)]

    def __eq__(self, other: "ColorSet") -> bool:
        if not isinstance(other, self.__class__):
            return False
        
        return (
            self.id == other.id and
            self.name == other.name and
            self.definition == other.definition and
            self.type == other.type and
            self.color == other.color
        )
    
    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"c={self.name}"
    
class Variable:
    def __init__(self, name: str, colorSet: ColorSet, id: str = None):
        self.name = name
        if not id:
            self.id = name
        else:
            self.id = id
        self.colorSet = colorSet

    def to_dict(self):
        return {"name": self.name, "id": self.id, "colorSet": self.colorSet.name}

    @classmethod
    def from_dict(cls, data: Dict, colorSets: list[ColorSet]):
        data["colorSet"] = Context._get_element(colorSets, data["colorSet"], "name")
        return cls(**data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (
            self.id == other.id and
            self.name == other.name and
            self.colorSet == other.colorSet
        )
    
    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"<{self.name}, {self.colorSet}>"

class Priority:
    def __init__(self, name: str, level: int, id: str):
        if not id:
            self.id = name
        else:
            self.id = id
        self.name = name
        self.level = level

    def to_dict(self):
        return vars(self)

    @staticmethod
    def low():
        return Priority(
            id="2a6b1d62-6df8-4f3c-ac1a-2b879869d30e", name="P_LOW", level=10000
        )

    @staticmethod
    def normal():
        return Priority(
            id="64b0e9d1-631f-4ce7-b3ca-577758c40b27", name="P_NORMAL", level=1000
        )

    @staticmethod
    def heigh():
        return Priority(
            id="6e9ed4ea-bedf-4423-934a-4fe1e21173a0", name="P_HEIGH", level=100
        )

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (
            self.id == other.id and
            self.name == other.name and
            self.level == other.level
        )
    def __repr__(self):
        return f"<{self.name}, {self.level}>"

class Function:
    def __init__(self, name: str, code: str, id: str = None):
        if not id:
            self.id = name
        else:
            self.id = id
        self.name = name
        self.code = code
        
    def to_dict(self):
        return vars(self)
    
    def __eq__(self, other: Function):
        return self.name == other.name

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
class Context:
    def __init__(
        self,
        colorSets: List[ColorSet] = None,
        variables: List[Variable] = None,
        priorities: List[Priority] = None,
        functions: List[Function] = None,
        uses: List[str] = None,
        values: List[str] = None,
        fusionSets: List[str] = None,
    ):
        self.colorSets = colorSets if colorSets is not None else []
        self.variables = variables if variables is not None else []
        self.priorities = priorities if priorities is not None else [
            Priority.low(),
            Priority.normal(),
            Priority.heigh(),
        ]
        self.functions = functions if functions is not None else []
        self.uses = uses if uses is not None else []
        self.values = values if values is not None else []
        self.fusionSets = fusionSets if fusionSets is not None else []
        self.variable_counters: dict[str, int] = {} #keys are colorSet prefixes
        self.mult_prefix = "MULT_"
        self.product_prefix = "PROD_"
        self.product_sep = "X"

    def add_colorSet(self, col: ColorSet):
        if col in self.colorSets:
            return
        self.colorSets.append(col)

    def add_function(self, func: Function, replace: bool = True):
        if func in self.functions and not replace:
            return
        elif func in self.functions:
            self.functions.remove(self.get_function(func))
        self.functions.append(func)

    def add_variable(self, var: Variable):
        self.variables.append(var)

    def get_variable_list(self):
        return self.variables

    def get_new_var_name(self, color: ColorSet = None) -> str:
        if color is None:
            return f"var{len(self.variables)+1}"
        
        var_prefix = ""
        if self.isMultColor(color):
            var_prefix = self.mult_prefix
            color = self.get_base_color_of_mult(color)

        color_prefix = var_prefix+color.name[:3]
        if color_prefix in self.variable_counters.keys():
            self.variable_counters[color_prefix] +=1
            num = self.variable_counters[color_prefix]
        else:
            self.variable_counters[color_prefix] = 1
            num = 1
        return f"{color_prefix}{num}"
        


    def create_new_var(self, color: str | ColorSet) -> Variable:
        if isinstance(color, str):
            color = self.get_color(color)
        var = Variable(self.get_new_var_name(), color)
        self.add_variable(var)
        return var

    @staticmethod
    def _get_element(list: list, key: str, by: str = "id") -> Any:
        for el in list:
            if getattr(el, by) == key:
                return el
        raise ValueError(f'No element of {by} "{key}"!')

    def get_color(self, key: str, by: str = "id") -> ColorSet:
        for col in self.colorSets:
            if getattr(col, by) == key:
                return col
        raise ValueError(f'No color of {by} "{key}"!')

    def get_mult_color(self, color: str | ColorSet) -> ColorSet:
        if isinstance(color, str):
            try:
                color = self.get_color(color)
            except ValueError:
                color = self.get_color(color, by="name")

        try:
            return self.get_color(self.mult_prefix + color.name, by="name")
        except ValueError:
            mult_col = ColorSet(
                self.mult_prefix + color.name,
                f"colset {self.mult_prefix+color.name} = list {color.name};",
                color=ColorSet.map_int_to_color(len(self.colorSets) + 1),
                type=ColorSetTypes.LIST
            )
            self.colorSets.append(mult_col)
            return mult_col
    
    def isMultColor(self, color: ColorSet):
        return color.type == ColorSetTypes.LIST

    def get_base_color_of_mult(self, color: ColorSet) -> ColorSet:
        if color.type != ColorSetTypes.LIST:
            return color
        name = color.definition.split("= list ")[1][0:-1]
        return self.get_color(name, by="name")

    def get_prod_color(self, color_a: str | ColorSet, color_b: str | ColorSet):
        if isinstance(color_a, str):
            color_a = self.get_color(color_a)
        if isinstance(color_b, str):
            color_b = self.get_color(color_b)

        prod_color_name = self.product_prefix + color_a.name+self.product_sep+color_b.name
        try:
            return self.get_color(prod_color_name, by="name")
        except ValueError:
            prod_color = ColorSet(
                name=prod_color_name,
                definition=f"colset {prod_color_name} = product {color_a.name} * {color_b.name};",
                color=ColorSet.map_int_to_color(len(self.colorSets) + 1),
                type=ColorSetTypes.PRODUCT
            )
            self.colorSets.append(prod_color)
            return prod_color

    def get_priority(self, key: str, by: str = "id") -> Priority:
        for prio in self.priorities:
            if getattr(prio, by) == key:
                return prio
        raise ValueError(f'No priority of {by} "{key}"!')

    def get_variable(self, key: str, by: str = "id") -> Variable:
        for var in self.variables:
            if getattr(var, by) == key:
                return var
        raise ValueError(f'No variable of {by} "{key}"!')

    def get_variable_by_color(self, color: ColorSet | str):
        if isinstance(color, str):
            color = self.get_color(color)
        for var in self.variables:
            if var.colorSet == color:
                return var
        
        # if the variable does not yet exist create it
        var = Variable(self.get_new_var_name(color),color)
        self.add_variable(var)
        return var
    
    def get_function(self, key: Function, by: str = "name") -> Function:
        for fun in self.functions:
            if getattr(fun, by) == getattr(key, by):
                return fun
        raise ValueError(f'No variable of {by} "{key}"!')
    
    def parse_variable_from_text(self, text: str) -> list[Variable]:
        variables: list[Variable] = []
        # sort variables by length so that string matching, tries longest strings first
        def compare_attr(var: Variable):
            return len(var.name)
        sorted_variables = sorted(self.variables,key=compare_attr, reverse=True)
        for var in sorted_variables:
            if text.__contains__(var.name):
                variables.append(var)
                text = text.replace(var.name, "")
        return variables
        
            
    @classmethod
    def from_dict(cls, data: Dict):
        colorSets = [ColorSet.from_dict(col) for col in data.get("colorSets", [])]
        variables = [
            Variable.from_dict(var, colorSets) for var in data.get("variables", [])
        ]
        priorities = [Priority.from_dict(el) for el in data.get("priorities", [])]
        functions = [
            Function.from_dict(fun) for fun in data.get("functions", [])
        ]
        uses = data.get("uses", [])
        values = data.get("values", [])
        fusionSets = data.get("fusionSets", [])
        instance = cls(
            colorSets=colorSets,
            variables=variables,
            priorities=priorities,
            functions=functions,
            uses=uses,
            values=values,
            fusionSets=fusionSets,
        )
        return instance