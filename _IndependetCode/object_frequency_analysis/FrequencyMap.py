import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_example_frequency_maps():
    # Typst examples:
    #
    # F^"Place Order"_"Item" = multset(3^2, 4^2, 6)
    # F^"Place Order"_"Discount" = multset(0^4, 1)

    plot_frequency_map(
        activity="Place Order",
        object_type="Item",
        freq_map={3: 2, 4: 2, 6: 1},
    )

    plot_frequency_map(
        activity="Place Order",
        object_type="Discount",
        freq_map={0: 4, 1: 1},
    )


def plot_frequency_map(activity: str, object_type: str, freq_map: dict[int, int]):
    """
    Create a Seaborn bar plot for a frequency map.

    x-axis: value, always ranging from 0 to 10
    y-axis: number of occurrences, always ranging from 0 to 6
    """

    output_dir = "_IndependetCode/object_frequency_analysis"
    os.makedirs(output_dir, exist_ok=True)

    # Create all values from 0 to 10 so that every value
    # gets its own position and tick on the x-axis.
    data = pd.DataFrame(
        {
            "value": range(11),
        }
    )

    data["occurrences"] = data["value"].map(freq_map).fillna(0)

    fig, ax = plt.subplots(figsize=(7, 4))

    sns.barplot(
        data=data,
        x="value",
        y="occurrences",
        ax=ax,
    )

    ax.set_xlabel("Value", fontsize=12)
    ax.set_ylabel("Number of occurrences", fontsize=12)

    ax.set_title(
        f"Frequency Set for {activity}, {object_type}",
        fontsize=15,
        pad=12,
    )

    # All values from 0 to 10 are now categorical positions,
    # so every tick is displayed and labeled.
    ax.set_xticks(range(11))
    ax.set_xticklabels(range(11))

    # Always use the full 0–6 range on the y-axis.
    ax.set_ylim(0, 6)
    ax.set_yticks(range(7))

    sns.despine(ax=ax)

    fig.tight_layout()

    filename = (
        f"_IndependetCode/object_frequency_analysis/"
        f"frequency_map_"
        f"{activity.lower().replace(' ', '_')}_"
        f"{object_type.lower().replace(' ', '_')}.svg"
    )

    fig.savefig(
        filename,
        format="svg",
        bbox_inches="tight",
    )

    plt.close(fig)


if __name__ == "__main__":
    plot_example_frequency_maps()