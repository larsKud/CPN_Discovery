import pytest
import json
import pandas
from CpnDiscovery.discover_cardinalities import *

class TestCardinalityDisc:

    def test_frequency_df(self):
        data_base_path = "tests/test_data/"
        file = "cardinality_test_data.csv"

        log = pm4py.read_ocel2(data_base_path+file)
        object_types = list(log.objects[log.object_type_column].unique())
        activities = list(log.events[log.event_activity].unique())
        frequency_df = get_object_frequencies(log, activities, object_types)
        
        assert frequency_df.loc[frequency_df['activity'] == 'A', 'frequencies'].values[0][2] == 3
        assert frequency_df.loc[frequency_df['activity'] == 'B', 'frequencies'].values[0][1] == 1
        assert frequency_df.loc[frequency_df['activity'] == 'B', 'frequencies'].values[0][3] == 2
        assert frequency_df.loc[frequency_df['activity'] == 'C', 'frequencies'].values[0][0] == 2
        assert frequency_df.loc[frequency_df['activity'] == 'E', 'frequencies'].values[0][6] == 1
        assert frequency_df.loc[frequency_df['activity'] == 'F', 'frequencies'].values[0][1] == 4


    def test_optional_discovery(self):
        data_base_path = "tests/test_data/"
        file = "cardinality_test_data.csv"


        log = pm4py.read_ocel2(data_base_path+file)
        object_types = list(log.objects[log.object_type_column].unique())
        activities = list(log.events[log.event_activity].unique())
        frequency_df = get_object_frequencies(log, activities, object_types)
        optional_ot = discover_optionality(frequency_df, optionality_threshold=0.3)
        opt_act = sorted([act.transition for act in optional_ot])

        assert str(opt_act) == str(['C', 'D'])
        
    def test_quantiles(self):
        test_cases = [
            (
                {1:1, 3:2, 2:1},
                0.25,
                1.75
            ),
            (
                {1:1, 3:2, 2:1},
                0.75,
                3
            ),
            (
                {1:2, 3:1, 4:1, 6:3},
                0.25,
                2
            ),
            (
                {1:2, 3:1, 4:1, 6:3},
                0.75,
                6
            )
        ]
        for freq_map, quantile, truth in test_cases:
            assert get_quantile(freq_map, quantile) == truth

    def test_narrow_variable_arcs(self):
        data_base_path = "tests/test_data/"
        file = "cardinality_test_data.csv"

        log = pm4py.read_ocel2(data_base_path+file)
        object_types = list(log.objects[log.object_type_column].unique())
        activities = list(log.events[log.event_activity].unique())
        frequency_df = get_object_frequencies(log, activities, object_types)
        
        variable_restrictions = discover_narrow_variable_arcs(frequency_df, method="min-max", threshold=0.0, include_optional=False)

        assert str(accessor("A", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("B", "transition", variable_restrictions).range) == str((1,3))
        assert str(accessor("C", "transition", variable_restrictions).range) == str((0,1))
        assert str(accessor("D", "transition", variable_restrictions).range) == str((0,2))
        assert str(accessor("E", "transition", variable_restrictions).range) == str((6,6))
        assert accessor("F", "transition", variable_restrictions) == None

        variable_restrictions = discover_narrow_variable_arcs(frequency_df, method="min-max", threshold=0.0, include_optional=True)

        assert str(accessor("A", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("B", "transition", variable_restrictions).range) == str((1,3))
        assert accessor("C", "transition", variable_restrictions) == None
        assert str(accessor("D", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("E", "transition", variable_restrictions).range) == str((6,6))
        assert accessor("F", "transition", variable_restrictions) == None

        variable_restrictions = discover_narrow_variable_arcs(frequency_df, method="iqr-rule", threshold=0.0, include_optional=True)

        assert str(accessor("A", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("B", "transition", variable_restrictions).range) == str((1,5))
        assert accessor("C", "transition", variable_restrictions) == None
        assert str(accessor("D", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("E", "transition", variable_restrictions).range) == str((6,6))
        assert accessor("F", "transition", variable_restrictions) == None

        variable_restrictions = discover_narrow_variable_arcs(frequency_df, method="quantile", threshold=0.5, include_optional=True)

        assert str(accessor("A", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("B", "transition", variable_restrictions).range) == str((2,2))
        assert accessor("C", "transition", variable_restrictions) == None
        assert str(accessor("D", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("E", "transition", variable_restrictions).range) == str((6,6))
        assert accessor("F", "transition", variable_restrictions) == None

        variable_restrictions = discover_narrow_variable_arcs(frequency_df, method="quantile", threshold=0.1, include_optional=True)

        assert str(accessor("A", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("B", "transition", variable_restrictions).range) == str((1,3))
        assert accessor("C", "transition", variable_restrictions) == None
        assert str(accessor("D", "transition", variable_restrictions).range) == str((2,2))
        assert str(accessor("E", "transition", variable_restrictions).range) == str((6,6))
        assert accessor("F", "transition", variable_restrictions) == None


def accessor(key, by, _list):
    for el in _list:
        if getattr(el, by) == key:
            return el
    return None
if __name__ == "__main__":
    tester = TestCardinalityDisc()
    tester.test_quantiles()