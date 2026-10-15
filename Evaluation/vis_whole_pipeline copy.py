import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_step_times(
    file_path="<dummypath>",
    save_path="",
):
    evalrun = file_path.split("/")[-1].split(".")[0]
    
    # 1. Load the evaluation results CSV
    df = pd.read_csv(file_path)

    # Strip ".sqlite" from dataset names
    df["dataset"] = df["dataset"].str.replace(".sqlite", "", regex=False)

    # 2. Identify all columns recording time in seconds
    step_columns = [col for col in df.columns if col.endswith("_seconds")]

    # 3. Reshape dataframe into long format
    df_long = df.melt(
        id_vars=["dataset", "run_slug"],
        value_vars=step_columns,
        var_name="step",
        value_name="seconds",
    )

    # Clean step labels
    df_long["step"] = (
        df_long["step"]
        .str.replace("_seconds", "", regex=False)
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    # Define color mapping for datasets
    dataset_colors = {
        "container_logistics": "#1f77b4",
        "order-management": "#ff7f0e",
        "ocel2-p2p": "#2ca02c",
        "lrms_02_p2p": "#d62728",
        "lrms_01_o2c": "#9467bd",
        "lrms_03_hiring": "#8c564b",
        "lrms_04_hospital": "#e377c2",
    }

    # 4. Set plot style
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 6))

    # 5. Create grouped bar plot with custom palette
    ax = sns.barplot(
        data=df_long,
        x="step",
        y="seconds",
        hue="dataset",
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