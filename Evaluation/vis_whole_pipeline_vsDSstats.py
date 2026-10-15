import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_evaluation_charts(dataset_stats_csv: str, evaluation_results_csv: str, result_dir: str):
    """
    Reads dataset stats and evaluation results, derives the dataset name from database_path, 
    merges them, computes total execution time and average objects per event, 
    scales events/objects/activities to thousands, and saves 4 separate SVG scatter plots 
    as well as 1 combined multi-panel chart with a shared legend.
    """
    # Create result directory if it doesn't exist
    os.makedirs(result_dir, exist_ok=True)
    
    # Load CSV files
    df_stats = pd.read_csv(dataset_stats_csv)
    df_eval = pd.read_csv(evaluation_results_csv)
    
    # Derive 'dataset' column in df_stats from 'database_path'
    if 'dataset' not in df_stats.columns and 'database_path' in df_stats.columns:
        df_stats['dataset'] = df_stats['database_path'].apply(lambda x: str(x).split("/")[-1].split(".")[0])
    
    # Merge df_stats into df_eval on the 'dataset' column
    if 'dataset' in df_eval.columns and 'dataset' in df_stats.columns:
        df_eval = pd.merge(df_eval, df_stats, on='dataset', how='inner', suffixes=('', '_stats'))
    else:
        raise ValueError("Unable to merge: 'dataset' column is missing or could not be derived from 'database_path'.")
    
    # Calculate total execution time by summing all duration columns ending with '_seconds'
    time_cols = [
        'loading_dataset_seconds', 'discover_ocpn_seconds', 'convert_ocpn_to_cpn_seconds',
        'restriction_object_frequencies_seconds', 'restriction_optionality_seconds',
        'restriction_narrow_variable_arcs_seconds', 'restriction_synchronization_seconds',
        'add_restrictions_seconds'
    ]
    existing_time_cols = [col for col in time_cols if col in df_eval.columns]
    df_eval['total_execution_time'] = df_eval[existing_time_cols].sum(axis=1)
    
    # Compute average objects per event if not already present in df_eval
    if 'avg_objects_per_event' not in df_eval.columns:
        if 'number_of_objects' in df_eval.columns and 'number_of_events' in df_eval.columns:
            df_eval['avg_objects_per_event'] = df_eval['number_of_objects'] / df_eval['number_of_events']

    # Scale events, objects, and activities to thousands for cleaner visualization
    scaling_map = {
        'number_of_events': 'number_of_events_k',
        'number_of_objects': 'number_of_objects_k',
        'number_of_activities': 'number_of_activities_k'
    }
    for orig_col, scaled_col in scaling_map.items():
        if orig_col in df_eval.columns:
            df_eval[scaled_col] = df_eval[orig_col] / 1000.0

    # Set Seaborn theme and 'tab10' palette
    sns.set_theme(style="whitegrid")
    palette = sns.color_palette("tab10")
    
    # Helper function for individual scatter plots
    def create_scatter_plot(x_col, title, filename, xlabel):
        if x_col not in df_eval.columns:
            print(f"Skipping {filename}: Column '{x_col}' not found in dataframe.")
            return
            
        plt.figure(figsize=(6, 5))
        sns.scatterplot(
            data=df_eval, 
            x=x_col, 
            y='total_execution_time', 
            hue='dataset', 
            palette=palette[:len(df_eval)], 
            s=100
        )
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel('Total Execution Time (seconds)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        output_path = os.path.join(result_dir, filename)
        plt.savefig(output_path, format='svg')
        plt.close()
        print(f"Saved: {output_path}")

    # Define the 4 metrics to plot
    metrics_config = [
        ('number_of_objects_k', 'Execution Time vs Number of Objects', 'execution_time_vs_objects.svg', 'Number of Objects (in thousands)'),
        ('number_of_events_k', 'Execution Time vs Number of Events', 'execution_time_vs_events.svg', 'Number of Events (in thousands)'),
        ('number_of_activities_k', 'Execution Time vs Number of Activities', 'execution_time_vs_activities.svg', 'Number of Activities (in thousands)'),
        ('avg_objects_per_event', 'Execution Time vs Avg Objects per Event', 'execution_time_vs_avg_objects.svg', 'Avg Objects per Event')
    ]

    # 1. Generate individual scatter plots
    for x_col, title, filename, xlabel in metrics_config:
        create_scatter_plot(x_col, title, filename, xlabel)

    # 2. Combined Multi-Panel Chart (2x2 grid) with a Shared Legend
    available_metrics = [m for m in metrics_config if m[0] in df_eval.columns]
    if len(available_metrics) == 4:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharey=True)
        axes = axes.flatten()
        
        for i, (x_col, title, _, xlabel) in enumerate(available_metrics):
            sns.scatterplot(
                data=df_eval,
                x=x_col,
                y='total_execution_time',
                hue='dataset',
                palette=palette[:len(df_eval)],
                s=100,
                ax=axes[i],
                legend=False  # We extract handles and add a single shared legend below
            )
            axes[i].set_title(title)
            axes[i].set_xlabel(xlabel)
            
            # Keep y-axis label only on the left column subplots (index 0 and 2)
            if i % 2 == 0:
                axes[i].set_ylabel('Total Execution Time (seconds)')
            else:
                axes[i].set_ylabel('')

        # Extract handles and labels from the first plot for the shared legend
        handles, labels = axes[0].get_legend_handles_labels()
        
        # Add a single shared legend to the right of the figure
        fig.legend(handles, labels, title='Dataset', bbox_to_anchor=(1.02, 0.5), loc='center left')
        
        plt.tight_layout()
        combined_output_path = os.path.join(result_dir, 'execution_time_combined_all.svg')
        plt.savefig(combined_output_path, format='svg', bbox_inches='tight')
        plt.close()
        print(f"Saved: {combined_output_path}")

if __name__ == "__main__":
    # Example usage:
    generate_evaluation_charts(
        dataset_stats_csv="/home/user/Documents/GitHub/MA/Evaluation/Results/db_stats261014_0845.csv",
        evaluation_results_csv="/home/user/Documents/GitHub/MA/Evaluation/Results/evaluation_261009_1052.csv",
        result_dir="./Evaluation/Charts"
    )