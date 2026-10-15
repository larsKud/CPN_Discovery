import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Color mapping for datasets
dataset_colors = {
    "container_logistics": "#1f77b4",
    "order-management": "#ff7f0e",
    "ocel2-p2p": "#2ca02c",
    "lrms_02_p2p": "#d62728",
    "lrms_01_o2c": "#9467bd",
    "lrms_03_hiring": "#8c564b",
    "lrms_04_hospital": "#e377c2",
}


def plot_step_times(
    file_path="<dummypath>",
    save_path="",
):
    evalrun = file_path.split("/")[-1].split(".")[0]
    # 1. Load the evaluation results CSV
    df = pd.read_csv(file_path)

    # Strip ".sqlite" from dataset names to match the color mapping keys
    df["dataset"] = df["dataset"].str.replace(".sqlite", "", regex=False)

    # Sort datasets by number of events (lowest to highest)
    # Assumes a column like 'num_events', 'events', or 'event_count' exists in the CSV.
    event_col = next(
        (col for col in ["number_of_events", "event_count", "events"] if col in df.columns),
        None,
    )
    if event_col:
        sorted_datasets = (
            df.groupby("dataset")[event_col]
            .mean()
            .sort_values()
            .index.tolist()
        )
    else:
        # Fallback ordering if no event column is found in the CSV
        sorted_datasets = sorted(df["dataset"].unique())

    # 1. Identify the columns ending with '_seconds'
    step_columns = [col for col in df.columns if col.endswith("_seconds")]

    # 2. Define your new column names
    new_names = [
        "Loading Dataset", 
        "Discover OCPN", 
        "Convert to CPN", 
        "Compute Frequency Maps", 
        "Discover Optionality", 
        "Discover Bounds", 
        "Discover Synchronization",  
        "Add Restriction to CPN"
    ]

    # 3. Create a mapping dictionary and rename the columns in the dataframe
    column_mapping = dict(zip(step_columns, new_names))
    df = df.rename(columns=column_mapping)
    
    # 3. Reshape dataframe into long format
    df_long = df.melt(
        id_vars=["dataset", "run_slug"],
        value_vars=new_names,
        var_name="step",
        value_name="seconds",
    )

    # Clean step labels
    if False:
        df_long["step"] = (
            df_long["step"]
            .str.replace("_seconds", "", regex=False)
            .str.replace("_", " ", regex=False)
            .str.title()
        )
    # 4. Set plot style
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 6))

    # 5. Create grouped bar plot with custom colors and sorted hue order
    ax = sns.barplot(
        data=df_long,
        x="step",
        y="seconds",
        hue="dataset",
        hue_order=sorted_datasets,
        palette=dataset_colors,
        errorbar=None,
    )
    ax.set_yscale("log")

    # 6. Customize plot labels and layout
    plt.title(
        "Execution Time per Step by Dataset (Log Scale)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    plt.xlabel("Step", fontsize=11, labelpad=10)
    plt.ylabel("Execution Time in Seconds (Log Scale)", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Dataset", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # 7. Save plot to PDF and SVG vector formats
    output_svg = save_path + "/" + evalrun + ".svg"
    plt.savefig(output_svg, format="svg", bbox_inches="tight")

    print(f"Plot saved successfully to '{output_svg}'.")
    plt.close()


if __name__ == "__main__":
    plot_step_times(
        "Evaluation/Results/evaluation_261009_1052.csv", "Evaluation/Charts"
    )