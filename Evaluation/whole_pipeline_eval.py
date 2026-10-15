import copy
import datetime
import os
import time
import traceback

import pandas as pd
import pm4py

from CpnDiscovery.Translator.translator import add_restrictions
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.discover_cardinalities import (
    discover_optionality,
    get_object_frequencies,
    discover_narrow_variable_arcs,
    delete_zero_object_frequencies,
)
from CpnDiscovery.o2o_sync import *


# ============================================================
# Configuration
# ============================================================

class EvalConfig:

    def __init__(
        self,
        database_file: str,
        syncPara,
        cardPara,
        run_slug: str,
        timeout: int = 1000,
    ):
        self.database_file = database_file
        self.syncPara = syncPara
        self.cardPara = cardPara
        self.run_slug = run_slug
        self.dataframe = pd.DataFrame()
        self.timeout = timeout

    def copy(self):
        return copy.deepcopy(self)


class SyncPara:

    def __init__(
        self,
        alpha: float,
        beta: float,
        useMin: bool = True,
        useResIdent: bool = True,
    ):
        self.alpha = alpha
        self.beta = beta
        self.useMin = useMin
        self.useResIdent = useResIdent


class CardPara:

    def __init__(
        self,
        program: str,
        threshold_opt: float,
        threshold_bound: float,
        method_bound: str,
    ):
        self.program = program
        self.threshold_opt = threshold_opt
        self.threshold_bound = threshold_bound
        self.method_bound = method_bound


default_eval = EvalConfig(
    database_file="",
    run_slug="",
    syncPara=SyncPara(
        alpha=1.0,
        beta=1.0,
        useMin=True,
        useResIdent=True,
    ),
    cardPara=CardPara(
        program="both",
        threshold_opt=0.2,
        threshold_bound=0.2,
        method_bound="minmax",
    ),
)


# ============================================================
# Datasets
# ============================================================

datasets_stick = [
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/order-management.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_01_o2c.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_03_hiring.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_04_hospital.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/enron_top_100000.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/container_logistics.sqlite"
    ]
datasets_laptop = [
        "/home/user/Documents/_MA/Data/order-management_shortend.sqlite"
    ]
datasets_pc = [
    "/home/user/Documents/MA_datasets/container_logistics.sqlite",
    "/home/user/Documents/MA_datasets/order-management.sqlite",
    "/home/user/Documents/MA_datasets/ocel2-p2p.sqlite",
    "/home/user/Documents/MA_datasets/lrms_02_p2p.sqlite",
    "/home/user/Documents/MA_datasets/lrms_01_o2c.sqlite",
    "/home/user/Documents/MA_datasets/lrms_03_hiring.sqlite",
    "/home/user/Documents/MA_datasets/lrms_04_hospital.sqlite",
]
datasets = datasets_pc

[
    "/home/user/Documents/MA_datasets/age_of_empires_ocel2.sqlite"
]


# ============================================================
# Output
# ============================================================

RESULTS_DIR = "./Evaluation/Results"


# ============================================================
# Dataset information
# ============================================================

def compute_general_dataset_information(log, db_path: str, result: dict):
    result["number_of_events"] = len(log.events)
    result["number_of_objects"] = len(log.objects)
    result["number_of_object_types"] = (
        log.objects[log.object_type_column].nunique()
    )
    result["number_of_activities"] = (
        log.events[log.event_activity].nunique()
    )



# ============================================================
# Restriction discovery
# ============================================================

def discover_restrictions(
    log: pm4py.OCEL,
    db_path: str,
    config: EvalConfig,
    timings: dict,
) -> RestrictionCollection:
    """
    Discover all restrictions.

    Every individual restriction-discovery step is timed separately.
    Timings are written into the supplied `timings` dictionary.
    """

    restrictions: RestrictionCollection = RestrictionCollection()

    # --------------------------------------------------------
    # Prepare values needed for cardinality restrictions
    # --------------------------------------------------------

    object_types = list(
        log.objects[log.object_type_column].unique()
    )

    activities = list(
        log.events[log.event_activity].unique()
    )

    # Object-frequency calculation
    start = time.perf_counter()

    frequency_df = get_object_frequencies(
        log,
        activities,
        object_types,
    )

    timings["restriction_object_frequencies_seconds"] = (
        time.perf_counter() - start
    )

    # --------------------------------------------------------
    # Cardinality restrictions
    # --------------------------------------------------------

    if config.cardPara.program in ("opt", "both"):

        start = time.perf_counter()

        restrictions.optional_ot = discover_optionality(
            frequency_df
        )

        timings["restriction_optionality_seconds"] = (
            time.perf_counter() - start
        )

    else:
        timings["restriction_optionality_seconds"] = 0.0

    # Remove zero frequencies before discovering bounds.
    delete_zero_object_frequencies(frequency_df)

    if config.cardPara.program in ("bound", "both"):

        start = time.perf_counter()

        restrictions.narrow_var_arcs = discover_narrow_variable_arcs(
            frequency_df,
            config.cardPara.method_bound,
            config.cardPara.threshold_bound,
        )

        timings["restriction_narrow_variable_arcs_seconds"] = (
            time.perf_counter() - start
        )

    else:
        timings["restriction_narrow_variable_arcs_seconds"] = 0.0

    # --------------------------------------------------------
    # Synchronization restrictions
    # --------------------------------------------------------

    if config.syncPara is not None:

        start = time.perf_counter()

        ot1s = get_non_ressource_object_types(db_path)

        restrictions.synchronizations = (
            discover_type_level_synchronization_top_down(
                database_file=db_path,
                alpha=config.syncPara.alpha,
                beta=config.syncPara.beta,
                ot1s=ot1s,
            )
        )

        timings["restriction_synchronization_seconds"] = (
            time.perf_counter() - start
        )

    else:
        timings["restriction_synchronization_seconds"] = 0.0

    return restrictions


# ============================================================
# CSV handling
# ============================================================

def save_results(results: list, output_file: str):
    """
    Save all results collected so far.

    This is called after every dataset so completed datasets remain
    available if a later dataset crashes.
    """

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)


# ============================================================
# Single dataset evaluation
# ============================================================

def run_discovery(config: EvalConfig) -> dict:
    """
    Run the complete evaluation for one dataset.

    Returns one dictionary containing all measurements for the dataset.
    """

    db_path = config.database_file

    dataset_name = os.path.basename(db_path)
    model_name = os.path.splitext(dataset_name)[0]

    result = {
        "run_slug": config.run_slug,
        "dataset": dataset_name,
        "database_file": db_path,
        "status": "success",
        "error": "",
    }

    timings = {}

    try:
        # ====================================================
        # 2.1 Loading Dataset
        # ====================================================

        start = time.perf_counter()

        log = pm4py.read_ocel2(db_path)

        timings["loading_dataset_seconds"] = (
            time.perf_counter() - start
        )

        # ====================================================
        # Optional: general dataset information
        # ====================================================

        # The actual implementation can later use the loaded log.
        # For now the function intentionally has an empty body.
        compute_general_dataset_information(
            log=log,
            db_path=db_path,
            result=result
        )

        # ====================================================
        # 2.2 Discovering OCPN with pm4py
        # ====================================================

        start = time.perf_counter()

        ocpn = pm4py.discover_oc_petri_net(log)

        timings["discover_ocpn_seconds"] = (
            time.perf_counter() - start
        )

        # ====================================================
        # 2.3 Converting OCPN to CPN
        # ====================================================

        start = time.perf_counter()

        cpn_proj = convert_ocpn_to_cpn(ocpn)

        timings["convert_ocpn_to_cpn_seconds"] = (
            time.perf_counter() - start
        )

        # ====================================================
        # 2.4 Discovering restrictions
        # ====================================================

        restriction_timings = {}

        restrictions = discover_restrictions(
            log=log,
            db_path=db_path,
            config=config,
            timings=restriction_timings,
        )

        timings.update(restriction_timings)

        # ====================================================
        # 2.5 Adding restrictions to model
        # ====================================================

        start = time.perf_counter()

        add_restrictions(
            restrictions,
            cpn_proj,
            expanded_var_arcs=False,
        )

        timings["add_restrictions_seconds"] = (
            time.perf_counter() - start
        )

        # ====================================================
        # 3. Export restricted model and restrictions
        # ====================================================

        os.makedirs("models", exist_ok=True)

        restrictions_path = (
            f"models/[delete]{model_name}_restrictions.json"
        )

        model_path = (
            f"models/[delete]{model_name}.ocpn"
        )

        restrictions.to_json(restrictions_path)

        cpn_proj.export_ocpn_json(model_path)

        # Exporting is intentionally NOT timed.

        result["restrictions_file"] = restrictions_path
        result["model_file"] = model_path

        result.update(timings)

    except Exception as e:
        # Preserve all timings that were successfully measured
        # before the error occurred.

        result.update(timings)

        result["status"] = "error"
        result["error"] = (
            f"{type(e).__name__}: {str(e)}"
        )

        # Store the traceback as well. This makes debugging failed
        # datasets much easier from the CSV.
        result["traceback"] = traceback.format_exc()

    return result


# ============================================================
# Main evaluation
# ============================================================

def main():

    run_slug = datetime.now().strftime(
        "%y%m%d_%H%M"
    )

    output_file = os.path.join(
        RESULTS_DIR,
        f"evaluation_{run_slug}.csv",
    )

    results = []

    for dataset in datasets:

        print("=" * 70)
        print(f"Evaluating dataset: {dataset}")
        print("=" * 70)

        config = default_eval.copy()

        config.run_slug = run_slug
        config.database_file = dataset

        result = run_discovery(config)

        results.append(result)

        # ----------------------------------------------------
        # IMPORTANT:
        # Save immediately after every dataset.
        # ----------------------------------------------------

        save_results(
            results,
            output_file,
        )

        if result["status"] == "success":
            print(f"Finished successfully: {dataset}")
        else:
            print(f"Failed: {dataset}")
            print(result["error"])

        print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()