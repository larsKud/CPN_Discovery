from CpnDiscovery.Translator.translator import add_restrictions
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.discover_cardinalities import discover_optionality, get_object_frequencies, discover_narrow_variable_arcs, delete_zero_object_frequencies
from CpnDiscovery.o2o_sync import *
import pandas as pd
import pm4py


debug = True

order_management = "order-management.sqlite"
om_lessOT = "order-management_lessOT.sqlite"
om_lessAct = "order-management_lessAct.sqlite"
om_short = "order-management_shortend.sqlite"
container_logistics = "container_logistics.sqlite"
ocel2_p2p = "ocel2-p2p.sqlite"
lrms_01 = "lrms_01_o2c.sqlite"
age_of_empires_ocel2 = "age_of_empires_ocel2.sqlite"
base_path_linux = "/home/user/Documents/MA_datasets/"
base_path_laptop = "/home/user/Documents/_MA/Data/"
base_path_laptop2 = "/run/media/user/FA7F-F7F4/_MA/Data/"

def discover_restrictions(log: pm4py.OCEL, db_path: str, config: dict) -> RestrictionCollection:
    restrictions: RestrictionCollection = RestrictionCollection()

    # Discover Cardinality Restrictions
    if config['cardinality']['active']:
        method = config['cardinality']['method']
        threshold = config['cardinality']['threshold']
        opt_threshold = config['cardinality']['opt_threhsold']

        object_types = list(log.objects[log.object_type_column].unique())
        activities = list(log.events[log.event_activity].unique())
        frequency_df = get_object_frequencies(log, activities, object_types)

        restrictions.optional_ot = discover_optionality(frequency_df, opt_threshold)
        delete_zero_object_frequencies(frequency_df)
        restrictions.narrow_var_arcs = discover_narrow_variable_arcs(frequency_df, method, threshold)

    # Discover Synchronizations
    if config['synchronization']['active']:
        #ot1s = get_ressource_pairs(db_path, 0.7)
        ot1s = ["customers"]
        restrictions.synchronizations = discover_type_level_synchronization_top_down(
            database_file=db_path, 
            alpha=config['synchronization']['alpha'],
            beta= config['synchronization']['beta'],
            ot1s=ot1s
            )

    return restrictions

def main():
    # initialize database access
    print("Loading dataset ...")
    database_name = om_lessOT
    db_path = base_path_laptop+database_name

    # load and discover log and ocpn
    model_name = database_name.split(".")[0]
    log = pm4py.read_ocel2(db_path)
    print("Discover model ...")
    ocpn = pm4py.discover_oc_petri_net(log)

    # convert ocpn to cpn
    cpn_proj = convert_ocpn_to_cpn(ocpn)
    print("Discovering restrictions ...")
    #discover restriction
    restriction_config = {
        'cardinality': {
            'active': True,
            'method': "iqr-rule",
            'threshold': 0.9,
            'opt_threhsold': 0.2
        },
        'synchronization': {
            'active': True,
            'alpha': 0.9,
            'beta': 1.0
        },
        'expand_var_arcs': False
    }
    restrictions = discover_restrictions(log, db_path, restriction_config)
    #save restriction to json
    restrictions.to_json(f"models/[delete]{model_name}_restrictions.json")
    print("Adding restriction to model ...")
    # add restrictions into cpn
    add_restrictions(restrictions, cpn_proj, expanded_var_arcs=False)
    print("Exporting restricted model ...")
    # save restricted model
    cpn_proj.export_ocpn_json(f"models/[delete]{model_name}.ocpn")

if __name__ == "__main__":
    main()