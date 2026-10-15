import pytest

from CpnDiscovery.MyCpn.Context import *

class TestContext:
    def test_colorset_creation(self):
        col = ColorSet(
            name="Color_1",
            definition="colset Color_1 = INT"
        )
        assert col.name == "Color_1"
        assert col.id == "Color_1"
        assert isinstance(col.color, str)

    def test_colorset_creation_from_dict(self):
        test_cases = [
            (
               {
                    "id": "25c5caee-6d3b-4510-93ee-60548e79bf4f",
                    "name": "INT",
                    "type": "basic",
                    "definition": "colset INT = int;",
                    "color": "#3b82f6"
                },
                ColorSet(
                    name="INT",
                    id="25c5caee-6d3b-4510-93ee-60548e79bf4f",
                    type=ColorSetTypes.BASIC,
                    definition="colset INT = int;",
                    color="#3b82f6"
                )
            ),
            (
               {
                "name": "MULT_INT",
                "type": "list",
                "definition": "colset MULT_INT = list INT;",
                "color": "hsl(99, 70%, 55%)",
                "timed": False,
                "id": "391605bf-2d5b-4c63-9578-567174f716d2"
                },
                ColorSet(
                    name="MULT_INT",
                    id="391605bf-2d5b-4c63-9578-567174f716d2",
                    type=ColorSetTypes.LIST,
                    definition="colset MULT_INT = list INT;",
                    color="hsl(99, 70%, 55%)"
                )
            )
        ]
        for _dict, truth in test_cases:
            assert ColorSet.from_dict(_dict) == truth

    def test_colorset_to_dict(self):
        col = ColorSet(
                    name="MULT_INT",
                    id="391605bf-2d5b-4c63-9578-567174f716d2",
                    type=ColorSetTypes.LIST,
                    definition="colset MULT_INT = list INT;",
                    color="hsl(99, 70%, 55%)"
                )
        truth = {
            'name': 'MULT_INT', 
            'id': '391605bf-2d5b-4c63-9578-567174f716d2', 
            'type': 'list', 
            'definition': 'colset MULT_INT = list INT;', 
            'color': 'hsl(99, 70%, 55%)', 
            'timed': False
            }
        assert col.to_dict() == truth

    def test_variable_creation_from_dict(self):
        color_list = [ 
            ColorSet("INT", "colset INT = int;"),
            ColorSet("MULT_INT", "colset MULT_INT = list INT;", type=ColorSetTypes.LIST),
            ]
        test_cases = [
            (
               {
                "id": "ID1412330717_0",
                "name": "x",
                "colorSet": "INT"
                },
                Variable(
                    name="x",
                    id="ID1412330717_0",
                    colorSet=color_list[0],
                )
            ),
            (
                {
                "name": "Xs",
                "colorSet": "MULT_INT",
                "id": "5dc278bb-0d6d-4b5c-8c0f-d890c4bdc2f3"
                },
                Variable(
                    name="Xs",
                    colorSet=color_list[1],
                    id="5dc278bb-0d6d-4b5c-8c0f-d890c4bdc2f3"
                )
            )
        ]
        for dict, truth in test_cases:
            assert Variable.from_dict(dict, color_list) == truth

    def test_variable_to_dict(self):
        var =  Variable(
                    name="Xs",
                    colorSet=ColorSet("MULT_INT", "colset MULT_INT = list INT;", type="list"),
                    id="5dc278bb-0d6d-4b5c-8c0f-d890c4bdc2f3"
                )
        truth = {
            'name': 'Xs', 
            'id': '5dc278bb-0d6d-4b5c-8c0f-d890c4bdc2f3', 
            'colorSet': 'MULT_INT'
            }
        assert var.to_dict() == truth

    def test_priority_from_dict(self):
        test_cases = [
            (
               {
                "id": "15513171-77b0-4f2d-aaeb-0137858ca372",
                "name": "P_HIGH",
                "level": 100
                },
                Priority(
                    name="P_HIGH",
                    id="15513171-77b0-4f2d-aaeb-0137858ca372",
                    level=100
                )
            )
        ]
        for dict, truth in test_cases:
            assert Priority.from_dict(dict) == truth


    def test_context(self):
        context = Context()
        c1 = ColorSet("RED", "colset RED = int", color="#f00")
        c2 = ColorSet("GREEN", "colset GREEN = int", color="#0f0")
        c3 = ColorSet("BLUE", "colset BLUE = int", color="#00f")
        assert len(context.colorSets) == 0
        context.add_colorSet(c1)
        assert context.colorSets[0].name == "RED"

        context.create_new_var(c1)
        context.create_new_var(c2)
        context.create_new_var(c3)
        assert(len(context.get_variable_list()) == 3)

        mult_c1 = context.get_mult_color(c1)
        assert mult_c1.name == "MULT_RED"
        assert mult_c1.name == context.get_color(mult_c1.id).name
        assert mult_c1.type == ColorSetTypes.LIST
        
        
    def test_parse_variables_from_text(self):
        context = Context()
        c1 = ColorSet("RED", "colset RED = int", color="#f00")
        c2 = ColorSet("GREEN", "colset GREEN = int", color="#0f0")
        var1 = Variable("v1", c1)
        var2 = Variable("v10", c2)
        var3 = Variable("v2", c2)
        var4 = Variable("v21", c1)
        context.add_variable(var1)
        context.add_variable(var2)
        context.add_variable(var3)
        context.add_variable(var4)
        
        text = f"{var1.name}"
        res = context.parse_variable_from_text(text)
        assert len(res) == 1
        assert res[0] == var1

        text = f"{var2.name} & {var1.name}.splice()"
        assert len(context.parse_variable_from_text(text)) == 2

        text = f"{var1} && {var2}gfh8ih {var3}-{var4}"
        res = context.parse_variable_from_text(text)
        assert len(res) == 4
        assert var1 in res
        assert var2 in res
        assert var3 in res
        assert var4 in res

        text = 'MULT_emp1'
        context = Context()
        c1 = ColorSet("employees", "colset employees = int", color="#f00")
        c2 = ColorSet("MULT_employees", "colset MULT_employees = list employees", color="#0f0")
        var2 = Variable("MULT_emp1", c2)
        var1 = Variable("emp1", c2)
        context.add_variable(var1)
        context.add_variable(var2)
        res = context.parse_variable_from_text(text)
        assert len(res) == 1
        assert res[0].name == text

if __name__ == "__main__":
    tester = TestContext()
    tester.test_parse_variables_from_text()