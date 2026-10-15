import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import ast

# Your input dictionary
csv_path = "/home/user/Documents/GitHub/MA/Evaluation/Results/db_stats261013_1140.csv"
df = pd.read_csv(csv_path)
data = ast.literal_eval(df.iloc[1]['object_type_stats'])
print(type(data))

# Extract object types and average events per object
object_types = list(data.keys())
avg_events = [val["avg_events_per_object"] for val in data.values()]

# Ensure the output directory exists
results_dir = "./Evaluation/Charts"
os.makedirs(results_dir, exist_ok=True)

# Set up the visualization style
plt.figure(figsize=(9, 5))
# Apply a clean publication-ready seaborn style
sns.set_theme(style="whitegrid", font_scale=1.1)
sns.set_theme(style="whitegrid")

# Define the colormap
UNIFIED_CMAP = "YlGnBu"

# Create a horizontal barplot with the requested palette
ax = sns.barplot(
    y=object_types, 
    x=avg_events, 
    palette=UNIFIED_CMAP, 
    hue=object_types
)

# Remove automatic legend if present
if ax.legend_ is not None:
    ax.legend_.remove()

# Make the horizontal bars slim
for patch in ax.patches:
    patch.set_height(0.4)

# Customize labels and title
plt.ylabel("Object Types", fontsize=12)
plt.xlabel("Average Events per Object", fontsize=12)
plt.title("Average Events per Object by Object Type", fontsize=14, pad=15)
plt.tight_layout()

# Save the chart
chart_path = os.path.join(results_dir, "avg_events_per_object_horizontal.png")
plt.savefig(os.path.join(results_dir, "events_objects.svg"), format="svg")
plt.close()

print(f"Horizontal chart successfully saved to: {chart_path}")

# Format DataFrame with the requested column names
df = pd.DataFrame([
    {"object type": k, "average events per object type": v["avg_events_per_object"]}
    for k, v in data.items()
])

# Save to CSV
csv_path = os.path.join(results_dir, "average_events_per_object.csv")
df.to_csv(csv_path, index=False)

print(f"CSV file successfully saved to: {csv_path}")