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

# Apply a clean publication-ready seaborn style
sns.set_theme(style="whitegrid", font_scale=1.1)

# Unified colormap for both heatmaps
UNIFIED_CMAP = "YlGnBu"

# =========================================================
# 1. Barplot: Execution time on y, pooled activities (a1 & a2) on x
# =========================================================
df_a1 = df[["a1", "timediff"]].rename(columns={"a1": "activity"})
df_a2 = df[["a2", "timediff"]].rename(columns={"a2": "activity"})
df_activities = pd.concat([df_a1, df_a2], ignore_index=True)

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
plt.title(
    "Mean Execution Time per Activity (Activities $a_1$ and $a_2$ Pooled)", pad=15
)
plt.xlabel("Activity", labelpad=10)
plt.ylabel("Execution Time (seconds)", labelpad=10)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "timediff_by_activity.svg"), format="svg")
plt.close()

# =========================================================
# 2. Barplot: Execution time on y, object type t1 on x
# =========================================================
df_t1_agg = (
    df.groupby("t1", as_index=False)["timediff"]
    .mean()
    .sort_values(by="timediff", ascending=False)
)

plt.figure(figsize=(8, 5))
sns.barplot(data=df_t1_agg, x="t1", y="timediff", palette="crest", hue="t1", legend=False)
plt.title("Mean Execution Time by Object Type", pad=15)
plt.xlabel("Object Type", labelpad=10)
plt.ylabel("Execution Time (seconds)", labelpad=10)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "timediff_by_t1.svg"), format="svg")
plt.close()

# =========================================================
# 3. Heatmap: a1 vs a2 colored by execution time
# =========================================================
pivot_a1_a2 = df.pivot_table(
    index="a1", columns="a2", values="timediff", aggfunc="mean"
)

plt.figure(figsize=(10, 8))
sns.heatmap(
    pivot_a1_a2,
    annot=True,
    fmt=".1f",
    cmap=UNIFIED_CMAP,
    linewidths=0.5,
    linecolor="white",
    cbar_kws={"label": "Execution Time (seconds)"},
)
plt.title("Activity $a_1$ vs. Activity $a_2$", pad=15)
plt.xlabel("Activity ($a_2$)", labelpad=10)
plt.ylabel("Activity ($a_1$)", labelpad=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "heatmap_a1_a2.svg"), format="svg")
plt.close()

# =========================================================
# 4. Heatmap: t1 vs t2 colored by execution time
# =========================================================
pivot_t1_t2 = df.pivot_table(
    index="t1", columns="t2", values="timediff", aggfunc="mean"
)

plt.figure(figsize=(8, 6))
sns.heatmap(
    pivot_t1_t2,
    annot=True,
    fmt=".1f",
    cmap=UNIFIED_CMAP,
    linewidths=0.5,
    linecolor="white",
    cbar_kws={"label": "Execution Time (seconds)"},
)
plt.title("Object Type $t_1$ vs. Object Type $t_2$", pad=15)
plt.xlabel("Object Type ($t_2$)", labelpad=10)
plt.ylabel("Object Type ($t_1$)", labelpad=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "heatmap_t1_t2.svg"), format="svg")
plt.close()

print(f"All updated SVGs successfully saved to the '{output_dir}' directory.")