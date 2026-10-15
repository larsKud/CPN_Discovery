import pytest
import json
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.Translator.translator import *

base_model_path = "tests/test_models/"
restr_base_path = "tests/test_restriction/"

class TestTranlator:

    def test_var_arc_expansion(self):
        model_name = "TheoreticallyCorrectVarArc"
        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        add_restrictions(restrictions=RestrictionCollection(), cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=True)
        res_cpn = cpn_p.cpns[0]
        #cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_expanded_var_arcs.ocpn")
        assert len(res_cpn.places) == 3
        assert len(res_cpn.transitions) == 3
        assert len(res_cpn.arcs) == 9

        model_name = "VarArcTest2"
        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        add_restrictions(restrictions=RestrictionCollection(), cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=True)
        res_cpn = cpn_p.cpns[0]
        #cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_expanded_var_arcs.ocpn")
        assert len(res_cpn.places) == 6
        assert len(res_cpn.transitions) == 7
        assert len(res_cpn.arcs) == 20

        model_name = "VarArcTest3"
        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        add_restrictions(restrictions=RestrictionCollection(), cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=True)
        res_cpn = cpn_p.cpns[0]
        cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_expanded_var_arcs.ocpn")
        assert len(res_cpn.places) == 4
        assert len(res_cpn.transitions) == 6
        assert len(res_cpn.arcs) == 18

    def test_variable_arc_restrictions(self):
        model_name = "ABC_NarrowVarArcTest"
        restr_name = "ABC_NarrowVarArc_Restrictions"
        output_model = True


        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=False)

        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_narVarArc.ocpn")

        #TODO assert that the guards are correct
        ta = cpn_p.cpns[0].get_transition("A", by="name")
        assert ta.guard == "(Xs.len() >= 1 && Xs.len() <= 11)"
        tb = cpn_p.cpns[0].get_transition("B", by="name")
        assert tb.guard == "(Xs.len() >= 2 && Xs.len() <= 2)"
        tc = cpn_p.cpns[0].get_transition("C", by="name")
        assert tc.guard == "(Xs.len() >= 8 && Xs.len() <= 12)"

    def test_optional_ots_restrictions(self):
        model_name = "ABC_NarrowVarArcTest"
        restr_name = "ABC_Optionality_Restriction"
        output_model = True


        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=False)

        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_optionality.ocpn")

        ta = cpn_p.cpns[0].get_transition("A", by="name")
        assert ta.guard == "((Xs.len() >= 1 && Xs.len() <= 11) || Xs.len() == 0)"
        tb = cpn_p.cpns[0].get_transition("B", by="name")
        assert tb.guard == "(Xs.len() != 0)"

    def test_synchronization_restrictions(self):
        #test simple sync setting
        model_name = "AB_Synchronized_CPN"
        restr_name = "AB_Synchronized_Restrictions"
        output_model = True


        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=False)

        restr_cpn = cpn_p.cpns[0]
        assert len(restr_cpn.places) == 7 #6 before +1
        assert len(restr_cpn.arcs) == 8+4 #TODO: Modifiey if delete arcs are introduced
        for arc in restr_cpn.arcs:
            assert arc.inscription.__contains__('<') == False
        for guard in restr_cpn.transitions:
            assert guard.guard.__contains__('<') == False
        
        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_sync.ocpn")

        # test mult variables on arcs
        model_name = "MultAB_Synchronized_CPNV2"
        restr_name = "AB_Synchronized_Restrictions"

        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=True)

        restr_cpn = cpn_p.cpns[0]
        assert len(cpn_p.context.functions) == 10

        blue_cleanup_trans = restr_cpn.get_transition('node_1786436442844', by="id")
        inc, outc = restr_cpn.get_arcs_from_transition(blue_cleanup_trans, by="id")

        assert len(outc) == 2

        for arc in outc:
            if len(arc.inscription) > 4:
                assert arc.inscription[0:7] == "remove2"

        for arc in restr_cpn.arcs:
            assert arc.inscription.__contains__('<') == False
        for guard in restr_cpn.transitions:
            assert guard.guard.__contains__('<') == False

        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_sync.ocpn")

        #TODO: test that by implication the emplyoee reaching the end does not clean up the synchronization (unless it's certain end)

        # test parallel synchronization
        model_name = "ABCD_Synchronized"
        restr_name = "ABCD_Synchronized_Restriction"

        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=True)

        restr_cpn = cpn_p.cpns[0]

        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"_added_sync.ocpn")
        
        sync_place = restr_cpn.get_place("p_sync_red_blue", by="name")
        inc, outg = restr_cpn.get_arcs_from_place(sync_place)
        assert len(inc) == 4
        assert len(outg) == 4

    def test_all_test(self):
        model_name = "AB_3Types_all_test"
        restr_name = "AB_3Types_all_test_Restrictions"
        output_model = True


        cpn_p = CPN_Project.import_ocpn_json(base_model_path+model_name+".ocpn")
        restr_col = RestrictionCollection.from_json(restr_base_path+restr_name+".json")
        
        add_restrictions(restrictions=restr_col, cpn_proj=cpn_p, format="ocpn", expanded_var_arcs=False)

        if output_model:
            cpn_p.export_ocpn_json(base_model_path+"[delete]"+model_name+"added_all.ocpn")

if __name__ == "__main__":
    tester = TestTranlator()
    tester.test_optional_ots_restrictions()