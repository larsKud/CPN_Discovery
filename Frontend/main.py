import json
import os
import pandas as pd
import streamlit as st
import altair as alt
from enum import Enum
import pm4py

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

from CpnDiscovery.Translator.translator import *
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.discover_cardinalities import discover_optionality, get_object_frequencies, discover_narrow_variable_arcs, delete_zero_object_frequencies
from CpnDiscovery.o2o_sync import *
from CpnDiscovery.queries import get_types

from Frontend.restriction_dashboard import render_dashboard

# ==========================================
# 2. DISCOVERY & BACKEND WRAPPERS
# ==========================================

def run_actual_discovery(db_path: str, config: dict) -> RestrictionCollection:
    """Executes the actual discovery algorithm if pm4py and modules are configured."""
    log = pm4py.read_ocel2(db_path)

    restrictions: RestrictionCollection = RestrictionCollection()

    # Discover Cardinality Restrictions
    if config['cardinality']['active'] or config['cardinality']['include_optional']:
        method = config['cardinality']['method']
        threshold = config['cardinality']['threshold']
        include_optional = config['cardinality']['include_optional']
        opt_threshold = config['cardinality']['opt_threshold']
        

        object_types = list(log.objects[log.object_type_column].unique())
        activities = list(log.events[log.event_activity].unique())
        frequency_df = get_object_frequencies(log, activities, object_types)

        

        if include_optional:
            restrictions.optional_ot = discover_optionality(frequency_df)
        if config['cardinality']['active']:
            restrictions.narrow_var_arcs = discover_narrow_variable_arcs(frequency_df, method, threshold, include_optional=include_optional)

    # Discover Synchronizations
    if config['synchronization']['active']:
        object_types = get_types(db_path)
        # ot1s should always be a list of non-resource objects
        try:
            ot1s = []
            for otype in object_types:
                if otype in config['synchronization']['resources']:
                    ot1s.append(otype)
        except Exception:
            ot1s = None

        restrictions.synchronizations = discover_type_level_synchronization_top_down(
            database_file=db_path, 
            alpha=config['synchronization']['alpha'],
            beta=config['synchronization']['beta'],
            ot1s=ot1s
        )

    return restrictions


def generate_mock_results() -> RestrictionCollection:
    """Fallback sample generator for testing/previewing UI without database files."""
    mock_data = {
        "narrow_var_arcs": [
            {"transition": "Create Order", "type": "input", "range": [1, 3], "otype": "Order"},
            {"transition": "Create Order", "type": "output", "range": [0, 5], "otype": "Item"},
            {"transition": "Process Payment", "type": "input", "range": [1, 1], "otype": "Payment"},
            {"transition": "Ship Package", "type": "output", "range": [1, 4], "otype": "Package"},
        ],
        "optional_ot": [
            {"transition": "Create Order", "otype": "Discount"},
            {"transition": "Process Payment", "otype": "Invoice"},
            {"transition": "Ship Package", "otype": "Insurance"},
        ],
        "synchronizations": [
            {"class_type": "SynchronizationRestriction", "transitions": ["Create Order", "Process Payment"], "sync_type": "IMPLICATION", "type_a": "Order", "type_b": "Payment"},
            {"class_type": "ExtendedSynchronizationRestriction", "transitions": ["Process Payment", "Ship Package"], "sync_type": "SYMETRIC", "type_a": "Payment", "type_b": "Package"},
        ]
    }
    return RestrictionCollection.from_dict(mock_data)


def main():
    st.set_page_config(page_title="Restriction Discovery Workbench", page_icon="⚡", layout="wide")

    # Guard: Initialize session state keys if they don't exist yet
    if "input_ocpn" not in st.session_state:
        st.session_state["input_ocpn"] = None
    if "discovered_restrictions" not in st.session_state:
        st.session_state["discovered_restrictions"] = None
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "model"
    if "selected_resources" not in st.session_state:
        st.session_state["selected_resources"] = []
    if "all_object_types" not in st.session_state:
        st.session_state["all_object_types"] = []
    if "non_resource_object_types" not in st.session_state:
        st.session_state["non_resource_object_types"] = []

    # Main layout: Configuration Form on Left / Preview & Results on Right
    col_config, col_main = st.columns([1, 2])

    with col_config:

        # --- Dataset / Path Settings ---
        with st.expander("Dataset & Model File Settings", expanded=True):
            db_path = st.text_input(
                "Database Filepath (.sqlite / .ocel)",
                value="/run/media/user/FA7F-F7F4/_MA/Data/order-management_shortend.sqlite",
                help="Absolute or relative filepath to the OCEL database file."
            )
            st.session_state['model_name'] = os.path.basename(db_path).split(".sql")[0]
            mock_mode = False

            # Cache / Compute object types in session state
            try:
                if db_path and os.path.exists(db_path):
                    st.session_state["all_object_types"] = get_types(db_path)
            except Exception:
                st.session_state["all_object_types"] = []

            # Custom CPN Option (Filepath only)
            use_custom_ocpn = st.checkbox("Load Custom CPN", value=False)
            custom_ocpn_path = ""
            if use_custom_ocpn:
                custom_ocpn_path = st.text_input(
                    "Custom CPN Filepath (.json / .ocpn)",
                    value="",
                    help="Filepath to custom CPN model file."
                )

            # Custom Restrictions Option (Filepath only)
            use_custom_restrictions = st.checkbox("Load Custom Restrictions", value=False)
            custom_restrictions_path = ""
            if use_custom_restrictions:
                custom_restrictions_path = st.text_input(
                    "Custom Restrictions JSON Filepath",
                    value="",
                    help="Filepath to pre-computed restrictions JSON file."
                )

        # --- Narrow Variable Arcs ---
        with st.expander("Bounded Variable Arcs", expanded=True):
            card_active = st.toggle("Active", value=True, key="card_active", disabled=use_custom_restrictions)
            
            card_method = st.selectbox(
                "Method",
                options=["min-max", "iqr-rule", "quantiles"],
                index=0,
                disabled=not card_active or use_custom_restrictions
            )
            if card_method == "quantiles":
                card_threshold = st.slider(
                    "Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.9,
                    step=0.01,
                    disabled=not card_active or use_custom_restrictions
                )
            else:
                card_threshold = 1.0

        # --- Optional Object Types ---
        with st.expander("Optional Object Types"):
            opt_ot_active = st.toggle("Active", value=True, key="opt_ot_active", disabled=use_custom_restrictions)
            opt_threshold = st.slider(
                "Optionality Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.01,
                disabled=not opt_ot_active or use_custom_restrictions
            )

        # --- Object Synchronization ---
        with st.expander("Object Synchronization", expanded=True):
            sync_active = st.toggle("Active", value=True, key="sync_active", disabled=use_custom_restrictions)

            # 1. Initialize the session state key for the multiselect if it doesn't exist yet
            if "selected_resources" not in st.session_state:
                st.session_state["selected_resources"] = st.session_state.get("all_object_types", [])

            # 2. Button to trigger resource identification FIRST (before the widget)
            identify_button = st.button(
                "Identify Resources", 
                disabled=not sync_active or use_custom_restrictions, 
                use_container_width=True
            )

            res_threshold = st.slider(
                "Ressource Threshold", min_value=0.0, max_value=1.0, value=0.9, step=0.05, 
                disabled=not sync_active or use_custom_restrictions,
                help="Threshold for when an object is counted as a ressource",
            )

            if identify_button:
                with st.spinner("Computing resource identification and object types..."):
                    try:
                        if os.path.exists(db_path):
                            non_res_types = get_non_ressource_object_types(db_path, res_threshold)
                            st.session_state["non_resource_object_types"] = non_res_types
                            
                            all_ots = st.session_state.get("all_object_types", [])
                            identified_resources = [ot for ot in all_ots if ot not in non_res_types] if non_res_types else []
                            
                            # Directly update the widget's session state key instead of a separate default variable
                            st.session_state["selected_resources"] = identified_resources
                            
                            st.success("Resource identification completed and stored in session state!")
                            st.rerun()
                        else:
                            st.error(f"Database filepath does not exist: '{db_path}'")
                    except Exception as e:
                        st.error(f"Resource identification failed: {e}")

            # 3. Input widget is bound directly via `key="selected_resources"` (remove `default`)
            selected_resources = st.multiselect(
                "Select Resources",
                options=st.session_state.get("all_object_types", []),
                key="selected_resources",
                disabled=not sync_active or use_custom_restrictions,
                help="Select resource object types for synchronization."
            )

            sync_alpha = st.slider(
                "Alpha", min_value=0.0, max_value=1.0, value=0.9, step=0.05, 
                disabled=not sync_active or use_custom_restrictions,
                help="Share of related event pairs that have to be synchronized in order to be considered significant."
            )
            sync_beta = 1.0
        # --- General Settings ---
        with st.expander("General Settings", expanded=True):
            expand_var_arcs = st.checkbox("Expand Variable Arcs", value=False)

        # Build Config Dict
        restriction_config = {
            'cardinality': {
                'active': card_active,
                'method': card_method,
                'threshold': card_threshold,
                'include_optional': opt_ot_active,
                'opt_threshold': opt_threshold
            },
            'synchronization': {
                'active': sync_active,
                'alpha': sync_alpha,
                'beta': sync_beta,
                'resources': st.session_state.get("selected_resources", []),
            },
            'expand_var_arcs': expand_var_arcs
        }

        st.divider()
        run_button = st.button("🚀 Run Discovery / Process", type="primary", use_container_width=True)

    with col_main:
        if run_button:
            with st.spinner("Processing Model and Restrictions..."):
                if mock_mode:
                    st.session_state["discovered_restrictions"] = generate_mock_results()
                    st.toast("Completed using mock data!")
                else:
                    try:
                        # --------------------------------------------------
                        # 1. OBTAIN RESTRICTIONS (Custom vs. Discovered)
                        # --------------------------------------------------
                        if use_custom_restrictions:
                            if custom_restrictions_path and os.path.exists(custom_restrictions_path):
                                print(f"Loading custom restrictions from filepath: {custom_restrictions_path}")
                                with open(custom_restrictions_path, "r") as f:
                                    restrictions_data = json.load(f)
                                st.session_state["discovered_restrictions"] = RestrictionCollection.from_dict(restrictions_data)
                            else:
                                st.error(f"Custom restrictions enabled, but the filepath is invalid or does not exist: '{custom_restrictions_path}'")
                                st.stop()
                        else:
                            if not os.path.exists(db_path):
                                st.error(f"Database filepath does not exist: '{db_path}'")
                                st.stop()
                            print(f"Discovering restrictions from database filepath: {db_path}")
                            st.session_state["discovered_restrictions"] = run_actual_discovery(db_path, restriction_config)

                        # --------------------------------------------------
                        # 2. OBTAIN CPN MODEL (Custom vs. Discovered)
                        # --------------------------------------------------
                        if use_custom_ocpn:
                            if custom_ocpn_path and os.path.exists(custom_ocpn_path):
                                print(f"Importing converted CPN directly from filepath: {custom_ocpn_path}")
                                cpn_proj = CPN_Project.import_ocpn_json(custom_ocpn_path)
                                st.session_state["input_ocpn"] = cpn_proj
                            else:
                                st.error(f"Custom CPN enabled, but the filepath is invalid or does not exist: '{custom_ocpn_path}'")
                                st.stop()
                        else:
                            if not os.path.exists(db_path):
                                st.error(f"Database filepath does not exist: '{db_path}'")
                                st.stop()
                            print(f"Discovering OCPN from OCEL database filepath: {db_path}")
                            log = pm4py.read_ocel2(db_path)
                            ocpn = pm4py.discover_oc_petri_net(log)

                            print("Converting OCPN model to CPN...")
                            cpn_proj = convert_ocpn_to_cpn(ocpn)
                            st.session_state["input_ocpn"] = cpn_proj

                        # --------------------------------------------------
                        # 3. APPLY RESTRICTIONS TO CPN
                        # --------------------------------------------------
                        if st.session_state["input_ocpn"] is not None and st.session_state["discovered_restrictions"] is not None:
                            print("Adding restrictions to CPN model...")
                            add_restrictions(st.session_state["discovered_restrictions"], st.session_state["input_ocpn"])
                            st.toast("Process completed successfully!")

                    except Exception as e:
                        st.error(f"Execution failed: {e}")

        # Display Results Dashboard if state contains discovered_restrictions and input_ocpn
        if st.session_state.get("discovered_restrictions") is not None:
            collection: RestrictionCollection = st.session_state["discovered_restrictions"]
            json_str = collection.to_json()

            # Guard against downloading before CPN model is set (e.g. in mock mode or error state)
            json_str2 = ""
            if st.session_state.get("input_ocpn") is not None:
                cpn_p: CPN_Project = st.session_state["input_ocpn"]
                temp_export_path = os.path.abspath(f"[temp]{st.session_state['model_name']}_restricted.ocpn")
                cpn_p.export_ocpn_json(temp_export_path)
                with open(temp_export_path, "r") as f:
                    json_str2 = f.read()

            with st.container(horizontal=True):
                st.download_button(
                    label="Download RestrictionCollection JSON",
                    data=json_str,
                    file_name="discovered_restrictions.json",
                    mime="application/json"
                )
                if json_str2:
                    st.download_button(
                        label="Download Restricted CPN",
                        data=json_str2,
                        file_name=f"{st.session_state['model_name']}_restricted.ocpn",
                        mime="application/json"
                    )

            render_dashboard(collection)
        else:
            st.info("👈 Adjust parameters on the left and click **Run Discovery / Process** to visualize the resulting restrictions.")


if __name__ == "__main__":
    main()