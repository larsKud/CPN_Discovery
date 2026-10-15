import json
import os
import pandas as pd
import streamlit as st
import altair as alt
from enum import Enum
import pm4py

from CpnDiscovery.Translator.translator import add_restrictions
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.discover_cardinalities import discover_optionality, get_object_frequencies, discover_narrow_variable_arcs, delete_zero_object_frequencies
from CpnDiscovery.o2o_sync import *

# ==========================================
# 3. DASHBOARD RENDERER
# ==========================================

def render_dashboard(collection: RestrictionCollection):
    st.subheader("Restriction Dashboard")

    # Tabs
    tab_overview, tab_cardinalities, tab_sync, ocpn_studio = st.tabs([
        "Overview Chart",
        "Cardinalities",
        "Synchronizations",
        "Ocpn Studio"
    ])

    df_arcs = pd.DataFrame([x.to_dict() for x in collection.narrow_var_arcs])
    if not df_arcs.empty:
        df_arcs["range_str"] = df_arcs["range"].apply(lambda r: f"[{r[0]}, {r[1]}]")

    df_opt = pd.DataFrame([x.to_dict() for x in collection.optional_ot])

    # Merge narrow variable arcs with optional indicator
    if not df_arcs.empty:
        df_cardinalities = df_arcs.copy()
        if not df_opt.empty:
            # Create a set of (transition, otype) pairs that are optional
            opt_set = set(zip(df_opt["transition"], df_opt["otype"]))
            df_cardinalities["optional"] = df_cardinalities.apply(
                lambda row: (row["transition"], row["otype"]) in opt_set, axis=1
            )
        else:
            df_cardinalities["optional"] = False
    else:
        df_cardinalities = pd.DataFrame()

    sync_dicts = []
    for s in collection.synchronizations:
        d = s.to_dict()
        d["transitions_str"] = ", ".join(d["transitions"])
        sync_dicts.append(d)
    df_sync = pd.DataFrame(sync_dicts)

# --- Tab 1: Charts ---
    with tab_overview:
        c1, c2 = st.columns(2)
        
        # Determine dynamic height based on item counts so both charts remain tall and readable
        # Calculate transition count
        t_card_list = []
        if not df_arcs.empty and "transition" in df_arcs.columns:
            t_card_list.extend(df_arcs["transition"].tolist())
        if not df_opt.empty and "transition" in df_opt.columns:
            t_card_list.extend(df_opt["transition"].tolist())
        t_sync_list = []
        if not df_sync.empty and "transitions" in df_sync.columns:
            for t_list in df_sync["transitions"]:
                if isinstance(t_list, list):
                    t_sync_list.extend(t_list)
        n_transitions = len(set(t_card_list + t_sync_list))

        # Calculate object type count
        o_card_list = []
        if not df_arcs.empty and "otype" in df_arcs.columns:
            o_card_list.extend(df_arcs["otype"].tolist())
        if not df_opt.empty and "otype" in df_opt.columns:
            o_card_list.extend(df_opt["otype"].tolist())
        o_sync_list = []
        if not df_sync.empty:
            if "type_a" in df_sync.columns:
                o_sync_list.extend(df_sync["type_a"].dropna().tolist())
            if "type_b" in df_sync.columns:
                o_sync_list.extend(df_sync["type_b"].dropna().tolist())
        n_otypes = len(set(o_card_list + o_sync_list))

        # Tall baseline height (600px minimum), expanding dynamically for large datasets
        chart_height = max(600, max(n_transitions, n_otypes) * 35)

        # -------------------------------------------------------------
        # Chart 1: Restrictions per Transition
        # -------------------------------------------------------------
        with c1:
            st.markdown("##### Restrictions per Transition")
            
            df_t_card = pd.Series(t_card_list).value_counts().reset_index()
            df_t_card.columns = ["Transition", "Count"]
            df_t_card["Restriction Type"] = "Cardinality"

            df_t_sync = pd.Series(t_sync_list).value_counts().reset_index()
            df_t_sync.columns = ["Transition", "Count"]
            df_t_sync["Restriction Type"] = "Synchronization"

            df_t_combined = pd.concat([df_t_card, df_t_sync], ignore_index=True)

            if not df_t_combined.empty:
                chart_trans = alt.Chart(df_t_combined).mark_bar(
                    cornerRadiusTopRight=3, 
                    cornerRadiusBottomRight=3
                ).encode(
                    x=alt.X("Count:Q", title="Count"),
                    y=alt.Y("Transition:N", sort="-x", title="Transition"),
                    yOffset="Restriction Type:N",
                    color=alt.Color(
                        "Restriction Type:N", 
                        scale=alt.Scale(domain=["Synchronization", "Cardinality"], range=["#4C78A8", "#F28E2B"]),
                        legend=alt.Legend(title="Restriction Type", orient="top")
                    ),
                    tooltip=["Transition", "Restriction Type", "Count"]
                ).properties(height=chart_height)

                st.altair_chart(chart_trans, use_container_width=True)
            else:
                st.info("No transition restrictions present.")

        # -------------------------------------------------------------
        # Chart 2: Restrictions per Object Type
        # -------------------------------------------------------------
        with c2:
            st.markdown("##### Restrictions per Object Type")

            df_o_card = pd.Series(o_card_list).value_counts().reset_index()
            df_o_card.columns = ["Object Type", "Count"]
            df_o_card["Restriction Type"] = "Cardinality"

            df_o_sync = pd.Series(o_sync_list).value_counts().reset_index()
            df_o_sync.columns = ["Object Type", "Count"]
            df_o_sync["Restriction Type"] = "Synchronization"

            df_o_combined = pd.concat([df_o_card, df_o_sync], ignore_index=True)

            if not df_o_combined.empty:
                chart_otype = alt.Chart(df_o_combined).mark_bar(
                    cornerRadiusTopRight=3, 
                    cornerRadiusBottomRight=3
                ).encode(
                    x=alt.X("Count:Q", title="Count"),
                    y=alt.Y("Object Type:N", sort="-x", title="Object Type"),
                    yOffset="Restriction Type:N",
                    color=alt.Color(
                        "Restriction Type:N", 
                        scale=alt.Scale(domain=["Synchronization", "Cardinality"], range=["#4C78A8", "#F28E2B"]),
                        legend=alt.Legend(title="Restriction Type", orient="top")
                    ),
                    tooltip=["Object Type", "Restriction Type", "Count"]
                ).properties(height=chart_height)

                st.altair_chart(chart_otype, use_container_width=True)
            else:
                st.info("No object type restrictions present.")

    # --- Tab 2: Cardinalities Table ---
    with tab_cardinalities:
        if not df_cardinalities.empty:
            st.dataframe(
                df_cardinalities[["transition", "otype", "range_str", "optional"]],
                column_config={
                    "transition": "Transition",
                    "otype": "Object Type",
                    "range_str": "Bounds [Lower, Upper]",
                    "optional": st.column_config.CheckboxColumn("Optional", default=False)
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No Cardinality Restrictions found.")

    # --- Tab 3: Synchronizations Table ---
    with tab_sync:
        if not df_sync.empty:
            # Helper function to format the synchronization column based on sync_type
            def format_sync_relation(row):
                # Handles enum values or string representations
                sync_type_val = str(row["sync_type"]).upper()
                if "IMPLICATION" in sync_type_val:
                    return f"{row['type_a']} ⇀ {row['type_b']}"
                elif "SYMETRIC" in sync_type_val or "SYMMETRIC" in sync_type_val:
                    return f"{row['type_a']} ⇌ {row['type_b']}"
                return f"{row['type_a']} ? {row['type_b']}"

            df_sync["Synchronization"] = df_sync.apply(format_sync_relation, axis=1)
            # Count the number of transitions in the list
            df_sync["transition_count"] = df_sync["transitions"].apply(len)

            df_display = df_sync[["Synchronization", "transitions_str", "transition_count"]].rename(
                columns={
                    "transitions_str": "Transitions",
                    "transition_count": "Transition Count"
                }
            )
            st.table(df_display)
        else:
            st.info("No Synchronizations found.")
    
    # --- Tab 4: OCPN-Studio ---
    with ocpn_studio:
        st.link_button("Ocpn Studio", "https://elte-dsed.github.io/ocpn-studio/")

# ==========================================
# 4. STREAMLIT MAIN APP
# ==========================================