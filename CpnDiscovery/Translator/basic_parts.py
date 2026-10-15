class ArcInscription:
    def __init__(self, otype: str, variables: list[Variable]):
        self.otype = otype # type of connecting place
        self.variables = variables

    def get_arc_inscription(self, format: str = "ocpn"):
        return f"{self.variables[0].name}"

