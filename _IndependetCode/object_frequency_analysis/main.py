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
activity = "pick item"

res_dict = {
      'activity': [],
      'otype': [],
      'frequencies': []
}
for activity in activity_list:
    filtered_data = data.loc[data['activity'] == activity]
    for ot in otypes:
        print(f"Working on {activity} - {ot}")
        res_dict['activity'].append(activity)
        res_dict['otype'].append(ot)
        res_dict['frequencies'].append({})
        for i in range(0,20):
            res_dict['frequencies'][-1][i] = 0
        for item in filtered_data[ot]:
            
            if isinstance(item, str):
                split_items = item.split("/")
                if isinstance(split_items, list):
                    item_count = len(split_items)
                    #add to res
                    try:
                        res_dict['frequencies'][-1][item_count] +=1
                    except:
                        res_dict['frequencies'][-1][item_count] = 1
            else:
                try:
                    res_dict['frequencies'][-1][0] +=1
                except:
                    res_dict['frequencies'][-1][0] = 1
res = pd.DataFrame(res_dict)
res.to_csv("./order_management_object_counts_v2")

