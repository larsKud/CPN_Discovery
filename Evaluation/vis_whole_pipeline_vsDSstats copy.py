import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def generate_evaluation_charts(dataset_stats_csv: str, evaluation_results_csv: str, result_dir: str):
    """
    Reads dataset stats and evaluation results, computes total execution time 
    and average objects per event, and saves 3 separate SVG scatter plots 
    as well as 1 combined side-by-side chart with a shared legend.
    """
    # Create result directory if it doesn't exist
    os.makedirs(result_dir, exist_ok=True)
    
    # Load CSV files
    df_stats = pd.read_csv(dataset_stats_csv)
    df_eval = pd.read_csv(evaluation_results_csv)
    
    # If the metrics are split across datasets, merge them on dataset name/path if needed.
    # Assuming df_eval contains columns: number_of_events, number_of_objects, etc.
    # Calculate total execution time by summing all duration columns ending with '_seconds'
    time_cols = [
        'loading_dataset_seconds', 'discover_ocpn_seconds', 'convert_ocpn_to_cpn_seconds',
        'restriction_object_frequencies_seconds', 'restriction_optionality_seconds',
        'restriction_narrow_variable_arcs_seconds', 'restriction_synchronization_seconds',
        'add_restrictions_seconds'
    ]
    # Filter columns that actually exist in the dataframe
    existing_time_cols = [col for col in time_cols if col in df_eval.columns]
    df_eval['total_execution_time'] = df_eval[existing_time_cols].sum(axis=1)
    
    # Compute average objects per event if not already present
    if 'avg_objects_per_event' not in df_eval.columns:
        if 'number_of_objects' in df_eval.columns and 'number_of_events' in df_eval.columns:
            df_eval['avg_objects_per_event'] = df_eval['number_of_objects'] / df_eval['number_of_events']
        elif 'total_objects' in df_stats.columns and 'total_events' in df_stats.columns:
            # Merge or map from stats if required
            pass

    # Set Seaborn theme and 'tab10' palette
    sns.set_theme(style="whitegrid")
    palette = sns.color_palette("tab10")
    
    # Formatter for thousands with 2 decimal places (e.g., 1.50K)
    k_formatter = FuncFormatter(lambda x, pos: f'{x * 1e-3:.1f}K')

    # Helper function for scatter plots (individual)
    def create_scatter_plot(x_col, title, filename, xlabel):
        plt.figure(figsize=(6, 5))
        sns.scatterplot(
            data=df_eval, 
            x=x_col, 
            y='total_execution_time', 
            hue='dataset', 
            palette=palette[:len(df_eval)], 
            s=100
        )
        
        # Apply K-formatting if the column represents events or objects
        if x_col in ['number_of_events', 'number_of_objects']:
            plt.gca().xaxis.set_major_formatter(k_formatter)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel('Total Execution Time (seconds)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        output_path = os.path.join(result_dir, filename)
        plt.savefig(output_path, format='svg')
        plt.close()
        print(f"Saved: {output_path}")

    # 1. Total Execution Time vs Number of Events
    if 'number_of_events' in df_eval.columns:
        create_scatter_plot(
            x_col='number_of_events',
            title='Execution Time vs Number of Events',
            filename='execution_time_vs_events.svg',
            xlabel='Number of Events'
        )

    # 2. Total Execution Time vs Number of Objects
    if 'number_of_objects' in df_eval.columns:
        create_scatter_plot(
            x_col='number_of_objects',
            title='Execution Time vs Number of Objects',
            filename='execution_time_vs_objects.svg',
            xlabel='Number of Objects'
        )

    # 3. Total Execution Time vs Avg Objects per Event
    if 'avg_objects_per_event' in df_eval.columns:
        create_scatter_plot(
            x_col='avg_objects_per_event',
            title='Execution Time vs Avg Objects per Event',
            filename='execution_time_vs_avg_objects.svg',
            xlabel='Avg Objects per Event'
        )

    # 4. Combined Side-by-Side Chart with a Shared Legend
    required_cols = ['number_of_events', 'number_of_objects', 'avg_objects_per_event']
    if all(col in df_eval.columns for col in required_cols):
        # Create a figure with 3 subplots side-by-side, sharing the Y-axis
        fig, axes = plt.subplots(1, 3, figsize=(10, 5), sharey=True)
        
        plots_config = [
            ('number_of_events', 'Execution Time vs Events', 'Number of Events'),
            ('number_of_objects', 'Execution Time vs Objects', 'Number of Objects'),
            ('avg_objects_per_event', 'Execution Time vs Avg Objects', 'Avg Objects per Event')
        ]
        
        for i, (x_col, title, xlabel) in enumerate(plots_config):
            sns.scatterplot(
                data=df_eval,
                x=x_col,
                y='total_execution_time',
                hue='dataset',
                palette=palette[:len(df_eval)],
                s=100,
                ax=axes[i],
                legend=(i == 2)  # Temporarily keep legend on the last subplot to extract handles/labels easily
            )
            
            # Apply K-formatting for events and objects axes in subplots
            if x_col in ['number_of_events', 'number_of_objects']:
                axes[i].xaxis.set_major_formatter(k_formatter)

            axes[i].set_title(title)
            axes[i].set_xlabel(xlabel)
            
            # Keep y-axis label only on the first subplot since they share the y-axis
            if i == 0:
                axes[i].set_ylabel('Execution Time (seconds)')
            else:
                axes[i].set_ylabel('')

        # Extract handles and labels from the last subplot and remove its individual legend
        handles, labels = axes[2].get_legend_handles_labels()
        axes[2].legend_.remove()
        
        # Add a single shared legend to the right of the figure
        fig.legend(handles, labels, title='Dataset', bbox_to_anchor=(1.01, 0.5), loc='center left')
        
        plt.tight_layout()
        combined_output_path = os.path.join(result_dir, 'execution_time_combined.svg')
        # bbox_inches='tight' prevents the external legend from getting cut off in the saved SVG
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