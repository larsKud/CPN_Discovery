import pytest
import json
import pandas
from CpnDiscovery.o2o_sync import *

class TestSyncDisc:
    def test_general_sync_discovery(self):
        base_path = "tests/sync_disc_test_data/"
        test_data = "test_datasets/"
        truth = "truths/"
        name = "SyncTestLog1"
        
        alpha: float = 0.5
        beta: float = 0.5
        if False:
            for table in ['synchronization_score', 'shared_object_pairs', 'candidate_event_pairs', 'event_pair_counts', 'eo_t2', 'eo_t1', 'objects_t2', 'objects_t1', 'events_a', 'events_b']:
                res2 = pd.DataFrame(debug_query(
                    database_file=base_path+test_data+name+".sqlite", 
                    activity1="place_order", 
                    activity2="place_order", 
                    type1="customers", 
                    type2="products",
                    table=table
                    ))
                res2.to_csv(f"SyncTest/[delete]_{table}.csv")

        res = run_new_sync_disc_query(base_path+test_data+name+".sqlite", alpha, beta)
        res.to_csv("./[delete]test_run_sync_disc.csv")
        truth = pd.read_csv(base_path+truth+name+".csv").iloc[:,-7:]
        print("Comparing Outputs")
        for i, row in truth.iterrows():
            print(row)
            a1, a2, t1, t2 ,tsr, tsb, tr = row 
            if not pd.notna(a1) or a1 is None:
                continue
            
            res_row = res.loc[(res['a1'] == a1) & (res['a2'] == a2) & (res['t1'] == t1) & (res['t2'] == t2)]

            if res_row.size != 0:
                rsr = list(res_row['sync_ratio'])[0]
                rsb = list(res_row['sync_bool'])[0]
                assert bool(rsb) == bool(tsb), f"{i} :[{a1},{a2}]-[{t1},{t2}] failed test with sync bool {rsb} should be {tsb}!"
            else:
                raise AssertionError(f"[{a1},{a2}]-[{t1},{t2}] should be present with sync bool {tsb}")
    
    
    def test_sync_discovery_noisy(self):      
        base_path = "tests/sync_disc_test_data/"
        test_data = "test_datasets/"
        truth = "truths/"
        name = "noisy_sync"
        
        alpha: float = 0.5
        beta: float = 0.5

        res = run_new_sync_disc_query(base_path+test_data+name+".sqlite", alpha, beta)
        res.to_csv("./[delete]test_run_sync_disc_noisy.csv")
        truth = pd.read_csv(base_path+truth+name+".csv")
        print("Comparing Outputs")
        for i, row in truth.iterrows():
            ti, a1, a2, t1, t2 ,tsr, tsb, tr = row 
            if not pd.notna(a1) or a1 is None:
                continue
            
            res_row = res.loc[(res['a1'] == a1) & (res['a2'] == a2) & (res['t1'] == t1) & (res['t2'] == t2)]

            if res_row.size != 0:
                rsr = list(res_row['sync_ratio'])[0]
                rsb = list(res_row['sync_bool'])[0]
                assert bool(rsb) == bool(tsb), f"{i} :[{a1},{a2}]-[{t1},{t2}] failed test with sync bool {rsb} should be {tsb}!"
                assert round(rsr,2) == round(tsr,2), f"{i} :[{a1},{a2}]-[{t1},{t2}] failed test with sync ratio {rsr} should be {tsr}!"
            else:
                raise AssertionError(f"[{a1},{a2}]-[{t1},{t2}] should be present with sync bool {tsb}")

    def test_ressource_identification(self):
        base_path = "tests/sync_disc_test_data/"
        test_data = "test_datasets/"
        truth = "truths/"
        name = "SyncTestLog1"
        
        alpha: float = 1
        beta: float = 1
        db_path = base_path+test_data+name+".sqlite"
        #res = run_new_sync_disc_query(db_path, alpha, beta)
        resource_pairs = get_ressource_pairs(db_path, threshold=0.8001)
        resource_pairs.to_csv("[delete]ressources_test.csv")
        assert list(resource_pairs["type1"])[0] == "products" 

        resource_pairs = {
            "type1": ["products"]*6,
            "type2": ["products", "orders", "items", "employees", "customers", "packages"]
        }
        resource_pairs = pd.DataFrame(resource_pairs)

        sync_res = run_new_sync_disc_query(db_path, 1.0, 1.0, resource_pairs, _csv_path="[delete]ressource_test_sync_run.csv")
        assert "products" not in sync_res['t1'].unique()

    def test_sync_disct_on_real_dataset(self):
        database_path = "tests/sync_disc_test_data/test_datasets/order-management_lessOT.sqlite"

        # Test if query runs
        query = "SELECT COUNT(*) FROM event"
        res = execute_query(query, database_path)
        assert res[0][0] == 21008

        query = "SELECT COUNT(*) FROM event_object"
        res = execute_query(query, database_path)
        assert res[0][0] == 75196

        query = "SELECT COUNT(*) FROM object"
        res = execute_query(query, database_path)
        assert res[0][0] == 10802

        test_cases = [
            (
                "pay order",
                "place order",
                "item",
                "order",
                0.7,
                1.0
            )
        ]
        for a1, a2, t1,t2, alpha, beta, truth in test_cases:
            res = new_synchronization_discovery()


if __name__ == "__main__":
    test = TestSyncDisc()
    test.test_ressource_identification()