import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import ast

# Load the CSV file
csv_path = "/home/user/Documents/GitHub/MA/Evaluation/Results/db_stats261013_1140.csv"
df = pd.read_csv(csv_path)

# Ensure the output directory exists
results_dir = "./Evaluation/Charts"
os.makedirs(results_dir, exist_ok=True)

# Define the visualization style and colormap
sns.set_theme(style="whitegrid", font_scale=1.1)
UNIFIED_CMAP = "tab10"

def extract_metric(val):
    """Safely extracts a numeric metric whether the value is a nested dict or a direct number."""
    if isinstance(val, dict):
        return val.get("avg_events_per_object", val.get("avg_events_per_activity", val.get("avg_events", 0)))
    elif isinstance(val, (int, float)):
        return val
    return 0

# ==========================================
# 1. PROCESS OBJECT TYPES
# ==========================================
obj_data = ast.literal_eval(df.iloc[1]['object_type_stats'])
object_types = list(obj_data.keys())
obj_avg_events = [extract_metric(val) for val in obj_data.values()]

figsize = (5,9)
# Chart: Object Types
plt.figure(figsize=figsize)
ax1 = sns.barplot(
    y=object_types, 
    x=obj_avg_events, 
    palette=UNIFIED_CMAP, 
    hue=object_types
)

if ax1.legend_ is not None:
    ax1.legend_.remove()


plt.ylabel("Object Types", fontsize=12)
plt.xlabel("Average Events per Object", fontsize=12)
plt.title("Average Events per Object by Object Type", fontsize=14, pad=15)
plt.tight_layout()

plt.savefig(os.path.join(results_dir, "events_objects.svg"), format="svg")
chart_path_obj = os.path.join(results_dir, "avg_events_per_object_horizontal.svg")
plt.savefig(chart_path_obj, format="svg")
plt.close()
print(f"Object types chart successfully saved to: {chart_path_obj}")

# Table & CSV: Object Types
df_obj = pd.DataFrame([
    {"object type": k, "average events per object type": extract_metric(v)}
    for k, v in obj_data.items()
])
csv_path_obj = os.path.join(results_dir, "average_events_per_object.csv")
df_obj.to_csv(csv_path_obj, index=False)
print(f"Object types CSV successfully saved to: {csv_path_obj}")


# ==========================================
# 2. PROCESS ACTIVITIES
# ==========================================
act_data = ast.literal_eval(df.iloc[1]['activity_event_counts'])
activities = list(act_data.keys())
act_values = [extract_metric(val) for val in act_data.values()]

# Chart: Activities (Vertical)
plt.figure(figsize=(12, 6))  # Slightly wider to accommodate rotated labels
ax2 = sns.barplot(
    x=activities, 
    y=act_values, 
    palette=UNIFIED_CMAP, 
    hue=activities
)

if ax2.legend_ is not None:
    ax2.legend_.remove()

plt.xlabel("Activities", fontsize=12)
plt.ylabel("Events", fontsize=12)
plt.title("Events per Activity", fontsize=14, pad=15)

# Angle the activity labels to prevent overlapping
plt.xticks(rotation=45, ha='right')

plt.tight_layout()

plt.savefig(os.path.join(results_dir, "events_activities.svg"), format="svg")
chart_path_act = os.path.join(results_dir, "events_per_activity_vertical.svg")
plt.savefig(chart_path_act, format="svg")
plt.close()
print(f"Activities chart successfully saved to: {chart_path_act}")

# Table & CSV: Activities
df_act = pd.DataFrame([
    {"activity": k, "events per activity": extract_metric(v)}
    for k, v in act_data.items()
])
csv_path_act = os.path.join(results_dir, "events_per_activity.csv")
df_act.to_csv(csv_path_act, index=False)
print(f"Activities CSV successfully saved to: {csv_path_act}")