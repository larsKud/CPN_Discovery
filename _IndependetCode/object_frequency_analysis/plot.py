import pandas as pd
import matplotlib.pyplot as plt
import ast
import math

def generate_activity_charts(csv_file):
    # 1. Load the data
    df = pd.read_csv(csv_file)

    # 2. Convert the 'frequencies' column from string strings like "[1,2,3]" to actual lists
    # This handles the list format provided in the CSV
    df['frequencies'] = df['frequencies'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    # 3. Get unique activities to create a separate chart for each
    activities = df['activity'].unique()

    for activity in activities:
        # Filter data for the specific activity
        act_df = df[df['activity'] == activity]
        otypes = act_df['otype'].unique()
        num_otypes = len(otypes)

        # 4. Set up the grid for subplots (2 columns, rows calculated based on number of otypes)
        cols = 2
        rows = math.ceil(num_otypes / cols)
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 5 * rows), squeeze=False)
        fig.suptitle(f'Activity Analysis: {activity}', fontsize=20, fontweight='bold')

        for i, otype in enumerate(otypes):
            ax = axes[i // cols, i % cols]
            
            # Combine all frequency lists for this activity + otype pair
            # (In case there are multiple rows for the same activity-otype combination)
            freq_data = act_df[act_df['otype'] == otype]['frequencies'].tolist()
            flat_list = [item for sublist in freq_data for item in sublist]
            
            # 5. Count how often each frequency value occurs
            counts = pd.Series(flat_list).value_counts().sort_index()
            
            # 6. Create the bar chart for the subfigure
            ax.bar(counts.index.astype(str), counts.values, color='skyblue', edgecolor='black')
            ax.set_title(f'Otype: {otype}', fontsize=14)
            ax.set_xlabel('Frequency Value (X)', fontsize=12)
            ax.set_ylabel('Occurrences (Y)', fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

        # Hide any empty subplots if the number of otypes is odd
        for j in range(i + 1, rows * cols):
            axes[j // cols, j % cols].axis('off')

        # Adjust layout and save the result
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        output_name = f'chart_{activity}.svg'
        plt.savefig(output_name, format="svg")
        print(f"Generated chart for activity '{activity}' as {output_name}")
        plt.close()

# Run the function with your CSV file name
generate_activity_charts('./order_management_object_counts.csv')