from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.MyCpn.Context import Context, Variable, ColorSet, Priority, Function, _get_element
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.Translator.translator_functions import *
from CpnDiscovery.Translator.basic_parts import *

class OTGuardPart:
    def __init__(self, otype: str, variable: Variable, range: tuple[int, int] = None, optional: bool = False, excludeOpt: bool = False):    
        self.otype = otype
        self.variable = variable
        self.lower_bound = None
        self.upper_bound = None
        if range:
            self.set_range(range)
        self.optional = optional
        self.excludeOpt = excludeOpt
    
    def set_range(self, range: tuple[int, int]):
        self.upper_bound = range[1]
        self.lower_bound = range[0]

    def create_guard_part(self, format:str = "ocpn"):
        range_part = ""
        optional_part = ""

        if format == "ocpn":
            if self.upper_bound:
                range_part = f"{self.variable.name}.len() >= {self.lower_bound} && {self.variable.name}.len() <= {self.upper_bound}"
            if self.optional:
                optional_part = f"{self.variable.name}.len() == 0"
            else:
                optional_part = f"{self.variable.name}.len() != 0"

            if self.excludeOpt and range_part != "":
                return f"{range_part}"
            elif self.excludeOpt:
                return f""

            if range_part != "" and self.optional: # range is specifed and is optional
                return f"({range_part}) || {optional_part}" 
            elif range_part != "": # range is specified and is not optional
                    return f"{range_part} && {optional_part}"
            elif not self.optional: # range is not specified and is not optional
                return f"{optional_part}"
            else:
                return ""
        else:
            raise NotImplementedError