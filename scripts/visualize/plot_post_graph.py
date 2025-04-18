"""plot_post_graph.py

Generate and save a NetworkX graph visualization for a single post's comment thread.

Usage
-----
python plot_post_graph.py <target_post_id> <input_csv_path> <output_dir>

Example
-------
python scripts/visualize/plot_post_graph.py \
    "Google__2025-03-04 12:33:00" \
    data/processed/master_data_graph_features.csv \
    docs/visualizations
"""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def plot_comment_graph(
    target_post_id: str, input_path: Path, output_dir: Path
) -> None:
    """Loads data, filters by post, builds graph, and saves plot."""

    LOGGER.info("Loading data from %s", input_path)
    if not input_path.exists():
        LOGGER.error("Input file not found: %s", input_path)
        return
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        LOGGER.error("Failed to read CSV: %s", e)
        return

    # Ensure required columns exist
    required = {"id", "parent_id", "source_post_id"}
    missing = required.difference(df.columns)
    if missing:
        LOGGER.error("Input data is missing required column(s): %s", missing)
        return

    LOGGER.info("Filtering for post_id: %s", target_post_id)
    grp = df[df["source_post_id"] == target_post_id].copy()

    if grp.empty:
        LOGGER.warning("No comments found for post_id: %s", target_post_id)
        return

    LOGGER.info("Building graph for %d comments...", len(grp))
    G = nx.DiGraph()
    for _, row in grp.iterrows():
        G.add_node(row["id"]) # Keep nodes simple for visualization
        pid = row["parent_id"]
        if pd.notna(pid) and pid in grp["id"].values:
            G.add_edge(pid, row["id"])

    # Identify roots for potential coloring/layout adjustments
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    node_colors = ["red" if n in roots else "lightblue" for n in G.nodes()]

    # Basic plotting
    plt.figure(figsize=(12, 12)) # Adjust figure size as needed
    # Use a layout that works well for trees/hierarchies if possible
    try:
        # Requires graphviz and pygraphviz/pydot
        # pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        # Fallback layouts
        pos = nx.spring_layout(G, k=0.5, iterations=50) # Spring layout as default
        # pos = nx.kamada_kawai_layout(G) # Alternative layout
    except Exception as e:
        LOGGER.warning("Layout calculation failed (%s), using basic spring layout.", e)
        pos = nx.spring_layout(G) # Default fallback

    nx.draw(
        G,
        pos,
        with_labels=False, # Labels can get very cluttered
        node_size=50,
        node_color=node_colors,
        arrowsize=5,
        alpha=0.8,
        width=0.5,
    )

    plt.title(f"Comment Graph for Post: {target_post_id}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = output_dir / f"{target_post_id.replace('__', '_')}_graph.png"

    try:
        plt.savefig(output_filename, dpi=300, bbox_inches="tight")
        LOGGER.info("Graph saved to %s", output_filename)
    except Exception as e:
        LOGGER.error("Failed to save plot: %s", e)
    finally:
        plt.close() # Close the plot to free memory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a visualization for a single post's comment graph."
    )
    parser.add_argument(
        "target_post_id", help="The source_post_id to visualize (e.g., 'Company__YYYY-MM-DD HH:MM:SS')"
    )
    parser.add_argument(
        "input_csv_path",
        type=Path,
        help="Path to the CSV file containing comments and graph features (e.g., data/processed/master_data_graph_features.csv)",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to save the output graph PNG image (e.g., docs/visualizations)",
    )
    args = parser.parse_args()

    plot_comment_graph(args.target_post_id, args.input_csv_path, args.output_dir)


if __name__ == "__main__":
    main() 