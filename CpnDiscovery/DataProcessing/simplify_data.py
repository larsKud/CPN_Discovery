import pandas as pd

db_path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order_management_ocel.csv"

data = pd.read_csv(db_path)
activity_list = [
    'place order', 
    'pick item',
    'item out of stock',
    'confirm order',
    'reorder item',
    'pay order', 
    'create package', 
    'send package',
    'package delivered', 
    'failed delivery', 
    'payment reminder',
    'o2o'
    ]
otypes = ['ot:orders', 'ot:items', 'ot:packages', 'ot:customers', 'ot:products', 'ot:employees']

# Synchronization is when a set of objects occure together
def preprocess_event_log_old():
    data = pd.read_csv(db_path)
    for i, row in data.iterrows():
        for ot in otypes:
            if not isinstance(row[ot], str):
                continue
            temp = row[ot].split("/")
            item_id_set = set()
            if isinstance(temp, list):
                for item in temp:
                    item_id = item.split("#")[0] # split unecessary info
                    if "{" in item_id:
                        item_id = item_id.split("{")[0] # remove meta information
                    item_id_set.add(item_id)
                

            
            data.at[i, ot] = str(item_id_set)
    data.to_csv("order_management_ocel_only_ids.csv")

if __name__ == "__main__":
    preprocess_event_log_old()