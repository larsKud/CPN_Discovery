db_path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order-management.sqlite"
name = "order_management"


import pprint
import os
import sqlite3
import pandas as pd
from pandarallel import pandarallel
from datetime import datetime

from CpnDiscovery.Node import *
from CpnDiscovery.queries import *
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.o2o_sync import *
dataset_pc = "/home/user/Documents/MA_datasets/order-management.sqlite"
#dataset_pc = "/home/user/Documents/MA_datasets/order-management_shortend.sqlite"
RESULTS_DIR = "./Evaluation/Results"

def main(db_path:str , save_path: str):
    dataset_name = os.path.basename(db_path)
    model_name = os.path.splitext(dataset_name)[0]

    run_slug = datetime.now().strftime(
        "%y%m%d_%H%M"
    )

    output_file = os.path.join(
        save_path,
        f"[delete]syncEval{run_slug}_{model_name}.csv",
    )
    alpha = 0.8
    beta = 1.0
    res = run_new_sync_disc_query(db_path, alpha, beta, _csv_path=output_file)

if __name__ == "__main__":
    main(dataset_pc, RESULTS_DIR)