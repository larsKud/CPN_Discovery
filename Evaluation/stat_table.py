import pandas as pd

db_path = "/home/user/Documents/GitHub/MA/Evaluation/Results/db_stats261014_0845.csv"
df = pd.read_csv(db_path)

# Vectorized string extraction (fastest and most idiomatic Pandas approach)
df['database'] = df['database_path'].astype(str).str.split('/').str[-1].str.split('.').str[0]
df.drop(columns=["database_path", "activity_event_counts", "object_type_stats", "error"], inplace=True)

# Save as a CSV (matching your .to_csv method)
output_path = db_path.split(".")[0] + "_processed.csv"
df.to_csv(output_path, index=False)