db_path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order-management.sqlite"
name = "order_management"


import pprint
import sqlite3
import pandas as pd
from pandarallel import pandarallel
from datetime import datetime
import time

from CpnDiscovery.Node import *
from CpnDiscovery.queries import *
from CpnDiscovery.Restrictions.restriction import *

def run_new_sync_disc_query(database_file: str, alpha: float = 0.5, beta: float = 0.5, resource_pairs: pd.DataFrame = None, _csv_path: str = None) -> pd.DataFrame:
    if _csv_path is not None:
        _save_to_csv = True
    else:
        _save_to_csv = False

    create_performance_indexes(database_file)
    res = get_a2o2(database_file)
    df: pd.DataFrame = pd.DataFrame(res)
    df.sort_values(by=[2,3,0,1],inplace=True)
    df.reset_index(inplace=True, drop=True)
    df.rename(columns={0:"a1",1:"a2", 2:"t1", 3:"t2"}, inplace=True)
    if resource_pairs is not None and ( not isinstance(resource_pairs, list)) and resource_pairs.shape[0] > 0:
        # filter out unwanted type_pairs e.g. excluding ressources
        df = (
            df.merge(
                resource_pairs,
                left_on=["t1", "t2"],
                right_on=["type1", "type2"],
                how="left",
                indicator=True,
            )
            .query('_merge == "left_only"')
            .drop(columns=["type1", "type2", "_merge"])
        )
    # df.to_csv(f"{_csv_path.split(".")[0]}_a2o2.csv") # should save the dataframe to csv but for some reason it does not work
    # Initialize pandarallel (uses all available CPU cores by default)
    pandarallel.initialize(progress_bar=True)

    # Define worker function for apply()
    def process_row(row):
        from CpnDiscovery.queries import new_synchronization_discovery
        
        if _save_to_csv:
            start = time.perf_counter()
        res = new_synchronization_discovery(
            activity1=row.iloc[0],
            activity2=row.iloc[1],
            type1=row.iloc[2],
            type2=row.iloc[3],
            database_file=database_file,
            alpha=alpha,
            beta=beta
        )
        if _save_to_csv:
            timediff = time.perf_counter() - start
            return res[0], timediff
        else:
            return res[0], None

    # Parallel execution using parallel_apply
    #df = df.sample(frac=1) #randomize so that work is spread evenly
    res_df = None
    dfs = []
    modulo = 100
    for i in range(0,len(df)//modulo+1):
        dfs.append(df.iloc[i*modulo:min(i*modulo+modulo,len(df))])

    for i, df in enumerate(dfs):
        print(f"\n---Working on ({i+1}/{len(dfs)})---")
        if len(df) == 0:
            continue
        df = df.sample(frac=1) #randomize so that work is spread evenly
        results = df.parallel_apply(process_row, axis=1) #executes the sql query calls in parallel
        print(f" Results {i+1}")
        results1 = [r[0] for r in results]
        timediffs = [r[1] for r in results]
        
        # Split the returned tuples back into DataFrame columns
        df['sync_ratio'] = [r[0] for r in results1]
        df['sync_bool'] = [r[1] for r in results1]
        df['num_phi_true'] = [r[2] for r in results1]
        df['total_candidate_pairs'] = [r[3] for r in results1]
        
        if _save_to_csv:
            df['timediff'] = [timediff for timediff in timediffs]

        if res_df is None:
            res_df = df
            if _save_to_csv:
                res_df.to_csv(_csv_path)
        else:
            res_df  = pd.concat([res_df,df])
            res_df.reset_index()
            if _save_to_csv:
                saved_df = pd.read_csv(_csv_path)
                saved_df = saved_df.iloc[:, -9:] #removes the indexes that are in the loaded dataframes
                saved_df = pd.concat([saved_df,df])
                saved_df.to_csv(_csv_path)
    return res_df
    

def discover_type_level_synchronization_top_down(database_file: str, alpha: float = 0.5, beta: float = 0.5, ot1s: pd.DataFrame | list = None) -> list[SynchronizationRestriction]:
    if ot1s is not None and not isinstance(ot1s, pd.DataFrame) and isinstance(ot1s, list) and len(ot1s) > 0:
        resource_pairs = {
            "type1": [],
            "type2": []
        }
        for ot1 in ot1s:
            for ot in get_types(database_file):
                resource_pairs['type1'].append(ot1)
                resource_pairs['type2'].append(ot)
        resource_pairs = pd.DataFrame(resource_pairs)
    else:
        resource_pairs = ot1s
    
    start_time = datetime.now()
    df = run_new_sync_disc_query(database_file, alpha, beta, resource_pairs)
    end_time = datetime.now()
    duration = end_time - start_time
    formatted_duration = (datetime.min + duration).strftime("%H:%M:%S")

    print(f"\nDuration:   {formatted_duration}")
    type_paris = []
    for t1 in df['t1'].unique():
        for t2 in df['t2'].unique():
            type_paris.append((t1,t2))

    df = df.loc[df['sync_bool']==1] # filter for true sync only

    restrictions: list[SynchronizationRestriction] = []
    symetric_pairs = []
    for t1, t2 in type_paris:
        filtered_df = df.loc[(df["t1"] == t1) & (df["t2"] == t2)]
        activities = set(filtered_df['a1'].unique()).union(set(filtered_df['a2'].unique()))
        #TODO: might be more prudent to expand it by explicit syncs. otherwise (A,B) (C,D) are combined to (A,B,C,D) even though a lot of intermediaries are missing
        #NOTE: Error
        flipped_df = df.loc[(df["t1"] == t2) & (df["t2"] == t1)]
        flipped_activities = set(flipped_df['a1'].unique()).union(set(flipped_df['a2'].unique()))
        
        if activities:
            sync_type = SyncType.IMPLICATION
            if activities == flipped_activities:
                sync_type = SyncType.SYMETRIC
                if set([t1,t2]) in symetric_pairs: #if pair was allready handled skip it
                    continue
                else:
                    symetric_pairs.append(set([t1,t2]))
            restrictions.append(
                SynchronizationRestriction(
                    transitions=activities,
                    sync_type=sync_type,
                    type_a=t1,
                    type_b=t2
                )
            )
    return restrictions

def get_ressource_pairs(database_file: str, threshold: float = 0.7):
    # create performance indexes for more efficienct SQL computation
    create_performance_indexes(database_file)

    object_types = get_types(database_file)
    res = {
        'type1': [],
        'type2': [],
        'is_resource': [],
        'ratio': []
    }
    print("Itentifying ressource types ...")
    for i1, type1 in enumerate(object_types):
        print(f"{(i1+1)*len(object_types)} / {len(object_types)*len(object_types)}")
        for i2, type2 in enumerate(object_types):
            if type1 == type2:
                continue
            pair_res = pd.DataFrame(is_ressource_type(type2, type1, threshold, database_file))
            res['type1'].append(type2)
            res['type2'].append(type1)
            res['is_resource'].append(pair_res.iloc[0,0])
            res['ratio'].append(pair_res.iloc[0,1])
    
    # if something is a ressource we also exclude self pairs
    self_pairs = {
        'type1': [],
        'type2': [],
        'is_resource': [],
        'ratio': []
    }
    for i,type1 in enumerate(res['type1']):
        if res['is_resource'][i] == 1 and type2 not in self_pairs['type1']:
            self_pairs['type1'].append(type2)
            self_pairs['type2'].append(type2)
            self_pairs['is_resource'].append(1)
            self_pairs['ratio'].append(None)

    for key in self_pairs.keys():
        res[key] += self_pairs[key]

    res = pd.DataFrame(res).sort_values(by='type1')
    print(f"Identified Ressources \n {list(res[res['is_resource'] == 1]["type1"].unique())}")
    res.to_csv('[delete]ressource_identification_results.csv')
    return res[res['is_resource'] == 1]

def get_non_ressource_object_types(database_file: str, threshold: float = 0.7):
    res = get_ressource_pairs(database_file=database_file, threshold=threshold)
    res_ots = list(res["type1"].unique())
    all_ots = get_types(database_file=database_file)
    non_res_ot = []
    for ot in all_ots:
        if ot not in res_ots:
            non_res_ot.append(ot)
    return non_res_ot

if __name__ == "__main__":
    order_management = "order-management.sqlite"
    container_logistics = "container_logistics.sqlite"
    ocel2_p2p = "ocel2-p2p.sqlite"
    age_of_empires_ocel2 = "age_of_empires_ocel2.sqlite"
    sync_test = "SyncTestLog1.sqlite"
    base_path_linux = "/run/media/user/FA7F-F7F4/_MA/Data/"
    base_path_laptop = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\"
    base_path_laptop2 = "/run/media/user/FA7F-F7F4/_MA/Data/"
    
    db_path = base_path_laptop2 + order_management
    
    resource_pairs = get_non_ressource_object_types(db_path)
    print(resource_pairs)

    alpha = 0.9
    beta = 0.7
    restrictions = discover_type_level_synchronization_top_down(db_path, alpha, beta, resource_pairs)
    # restrictions = discover_type_level_synchronization(db_path, alpha, beta)

    print("---- SYNC DISCOVERY COMPLETE ------------")
    for res in restrictions:
        print(res)

    #discover_o2o_initial()