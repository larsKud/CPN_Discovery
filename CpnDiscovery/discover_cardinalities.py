from CpnDiscovery.Translator.translator import add_restrictions
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
import pandas as pd
import pm4py
import math

debug = False


def get_stats(freq_map):
    # Filter out zero frequencies and sort by value
    data = sorted([(val, count) for val, count in freq_map.items() if count > 0])

    if not data:
        return None, None

    values = [item[0] for item in data]
    counts = [item[1] for item in data]

    # Min and Max
    minimum = values[0]
    maximum = values[-1]
    return minimum, maximum

def get_quantile(freq_map: dict, p: float):
    if not (0 <= p <= 1):
        raise ValueError("p must be between 0 and 1")

    # Filter non-positive counts and sort by value
    data = sorted([(val, count) for val, count in freq_map.items() if count > 0])
    if not data:
        return None

    N = sum(count for _, count in data)

    if N == 1 or p == 0:
        return float(data[0][0])
    if p == 1:
        return float(data[-1][0])

    # Excel PERCENTILE.INC 1-based target rank: 1 + p * (N - 1)
    target_rank = 1.0 + p * (N - 1)

    cumulative = 0
    for i, (val, count) in enumerate(data):
        prev_cumulative = cumulative
        cumulative += count

        if target_rank <= cumulative:
            # Case 1: Target falls strictly inside a repeated value bucket (e.g. between rank 3.0 and 4.0 for value 3)
            if target_rank <= prev_cumulative + 1:
                if i == 0:
                    return float(val)
                
                # Target is between rank (prev_cumulative) [val_prev] and (prev_cumulative + 1) [val_curr]
                prev_val = data[i - 1][0]
                fraction = target_rank - prev_cumulative  # Progress from prev_val to val
                return float(prev_val + fraction * (val - prev_val))

            # Case 2: Target rank is > prev_cumulative + 1, meaning it lands entirely within identical duplicate values
            return float(val)

    return float(data[-1][0])

def get_object_frequencies(
    log: pm4py.OCEL, activities: list[str], object_types: list[str]
) -> pd.DataFrame:
    res_dict = {"activity": [], "otype": [], "frequencies": []}
    ot_prefix = "ocel:type:"
    data = log.get_extended_table(ot_prefix=ot_prefix)
    for activity in activities:
        filtered_data = data.loc[
            data[log.event_activity] == activity
        ]  # filter log for activity
        for ot in object_types:  # go through all object types and count the frequency
            if debug:
                print(f"Working on {activity} - {ot}")

            res_dict["activity"].append(activity)
            res_dict["otype"].append(ot)
            res_dict["frequencies"].append({})
            for item in filtered_data[ot_prefix + ot]:
                if isinstance(item, list):
                    item_count = len(item)
                    # add to res
                    try:
                        res_dict["frequencies"][-1][item_count] += 1
                    except:
                        res_dict["frequencies"][-1][item_count] = 1
                else:
                    try:
                        res_dict["frequencies"][-1][0] += 1
                    except:
                        res_dict["frequencies"][-1][0] = 1
    res = pd.DataFrame(res_dict)
    return res


def discover_optionality(
    object_frequencies: pd.DataFrame, optionality_threshold: float = 0.1, 
) -> list[OptionalOTRestriction]:
    simple_res = []
    for i, row in object_frequencies.iterrows():
        activity = row["activity"]
        otype = row["otype"]
        frequencies: dict = row["frequencies"]

        if 0 in frequencies.keys() and len(frequencies.keys()) > 1:
            # 0 is an option and there is another non zero option
            counts = 0
            for val in frequencies.values():
                counts += val
            if frequencies[0] / counts >= optionality_threshold:
                restriction = OptionalOTRestriction(
                    transition=activity,
                    otype=otype
                )
                simple_res.append(restriction)
    return simple_res


def delete_zero_object_frequencies(object_frequencies: pd.DataFrame):
    # frequencies of only 0 or of an already handled optionality should no longer consider 0. Therefore delete 0 from all object frequencies
    # operation is handled in place
    for i, row in object_frequencies.iterrows():
        if 0 in object_frequencies.loc[i, "frequencies"]:
            del object_frequencies.loc[i, "frequencies"][0]


def discover_narrow_variable_arcs(
    object_frequencies: pd.DataFrame,
    method: str = "min-max",
    threshold: float = 0.1,
    include_optional: bool = True,
):
    if include_optional:
        delete_zero_object_frequencies(object_frequencies)
    restrictions = []
    for i, row in object_frequencies.iterrows():
        activity = row["activity"]
        otype = row["otype"]
        frequencies: dict = row["frequencies"]

        if len(frequencies) == 0:
            continue

        upper, lower = (0, 0)
        if method == "min-max":
            lower, upper = get_stats(frequencies)
        elif method == "iqr-rule":
            thrid_quartal = get_quantile(frequencies, 0.75)
            first_quartal = get_quantile(frequencies, 0.25)
            wisker_len = (thrid_quartal - first_quartal) * 1.5
            upper = round(thrid_quartal + wisker_len)

            alt = 0
            if include_optional:
                alt = 1
            lower = max(round(first_quartal - wisker_len), alt)
        elif method == "quantile":
            upper = round(get_quantile(frequencies, 1 - threshold))
            lower = round(get_quantile(frequencies, threshold))

        if upper == lower: 
            if upper == 1:
                continue 
            type = 'exact'
        else:
            type = 'range'
        restriction = NarrowVariableArcRestriction(
            transition=activity,
            type=type,
            range=[lower, upper],
            otype=otype,
        )
        restrictions.append(restriction)

    return restrictions


def discover_restrictions(log: pm4py.OCEL) -> RestrictionCollection:
    restrictions: RestrictionCollection = RestrictionCollection()
    method = "min-max"
    threshold = 0.9

    object_types = list(log.objects[log.object_type_column].unique())
    activities = list(log.events[log.event_activity].unique())
    frequency_df = get_object_frequencies(log, activities, object_types)

    restrictions.optional_ot = discover_optionality(frequency_df)
    delete_zero_object_frequencies(frequency_df)
    restrictions.narrow_var_arcs = discover_narrow_variable_arcs(frequency_df, method, threshold)
    return restrictions

if __name__ == "__main__":
    db_path = (
        "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order-management.sqlite"
    )
    model_name = "order_management"
    log = pm4py.read_ocel2(db_path)
    ocpn = pm4py.discover_oc_petri_net(log)
    cpn_proj = convert_ocpn_to_cpn(ocpn)
    restrictions = discover_restrictions(log)
    add_restrictions(restrictions, cpn_proj)
    cpn_proj.export_ocpn_json(f"models\\[delete]{model_name}.ocpn")
