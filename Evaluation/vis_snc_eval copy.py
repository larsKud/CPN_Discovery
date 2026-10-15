import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 1. Setup output directory
output_dir = "./Evaluation/Charts"
os.makedirs(output_dir, exist_ok=True)

# 2. Load dataset (replace 'your_data.csv' with your actual file path)
csv_path = "/home/user/Documents/GitHub/MA/Evaluation/Results/syncEval261012_2342_order-management.csv"
df = pd.read_csv(csv_path)

# Apply a clean seaborn style
sns.set_theme(style="whitegrid")

# =========================================================
# 1. Barplot: timediff on y, pooled activities (a1 & a2) on x
# =========================================================
# Melt a1 and a2 into a single column since order is irrelevant
df_a1 = df[["a1", "timediff"]].rename(columns={"a1": "activity"})
df_a2 = df[["a2", "timediff"]].rename(columns={"a2": "activity"})
df_activities = pd.concat([df_a1, df_a2], ignore_index=True)

# Aggregate (mean) timediff by activity and sort
df_act_agg = (
    df_activities.groupby("activity", as_index=False)["timediff"]
    .mean()
    .sort_values(by="timediff", ascending=False)
)

plt.figure(figsize=(10, 6))
sns.barplot(
    data=df_act_agg,
    x="activity",
    y="timediff",
    palette="viridis",
    hue="activity",
    legend=False,
)
plt.title("Average Timediff by Activity (a1 and a2 Pooled)")
plt.xlabel("Activity")
plt.ylabel("Timediff")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "timediff_by_activity.svg"), format="svg")
plt.close()

# =========================================================
# 2. Barplot: timediff on y, t1 on x
# =========================================================
df_t1_agg = (
    df.groupby("t1", as_index=False)["timediff"]
    .mean()
    .sort_values(by="timediff", ascending=False)
)

plt.figure(figsize=(8, 5))
sns.barplot(data=df_t1_agg, x="t1", y="timediff", palette="crest", hue="t1", legend=False)
plt.title("Average Timediff by t1")
plt.xlabel("t1")
plt.ylabel("Timediff")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "timediff_by_t1.svg"), format="svg")
plt.close()

# =========================================================
# 3. Heatmap: a1 vs a2 colored by timediff
# =========================================================
pivot_a1_a2 = df.pivot_table(
    index="a1", columns="a2", values="timediff", aggfunc="mean"
)

plt.figure(figsize=(10, 8))
sns.heatmap(pivot_a1_a2, annot=True, fmt=".1f", cmap="YlGnBu", cbar=True)
plt.title("Heatmap of Timediff: a1 vs a2")
plt.xlabel("a2")
plt.ylabel("a1")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "heatmap_a1_a2.svg"), format="svg")
plt.close()

# =========================================================
# 4. Heatmap: t1 vs t2 colored by timediff
# =========================================================
pivot_t1_t2 = df.pivot_table(
    index="t1", columns="t2", values="timediff", aggfunc="mean"
)

plt.figure(figsize=(8, 6))
sns.heatmap(pivot_t1_t2, annot=True, fmt=".1f", cmap="Blues", cbar=True)
plt.title("Heatmap of Timediff: t1 vs t2")
plt.xlabel("t2")
plt.ylabel("t1")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "heatmap_t1_t2.svg"), format="svg")
plt.close()

print(f"All SVGs successfully saved to the '{output_dir}' directory.")