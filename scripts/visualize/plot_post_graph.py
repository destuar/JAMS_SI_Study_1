"""plot_post_graph.py

Generate and save NetworkX graph visualizations for one representative
comment thread from each target company (Delta, Costco, Target, Google).

Usage
-----
python plot_post_graph.py <input_csv_path> <output_dir>

Example
-------
python scripts/visualize/plot_post_graph.py \
    data/derived/graphed_comments.csv \
    results/figures
"""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Define target companies
TARGET_COMPANIES = ['Delta', 'Costco', 'Target', 'Google']

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def select_representative_posts(df: pd.DataFrame) -> dict[str, str]:
    """Selects one representative source_post_id per company."""
    if 'source_post_id' not in df.columns:
        # Try to construct it if missing (should exist in graphed_comments.csv)
        if 'company_name' in df.columns and 'post_date' in df.columns:
            LOGGER.warning("'source_post_id' column missing, constructing from company and post_date.")
            # Ensure post_date is datetime
            df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce")
            df["source_post_id"] = (
                df["company_name"].astype(str) + "__" + df["post_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
             raise ValueError("Cannot select posts: Missing 'source_post_id' or columns to construct it.")

    if 'depth' not in df.columns:
         raise ValueError("Cannot select posts: Missing 'depth' column.")

    LOGGER.info("Calculating stats per post to select examples...")
    post_stats = df.groupby(['company_name', 'source_post_id']).agg(
        comment_count=('id', 'size'),
        max_depth=('depth', 'max')
    ).reset_index()

    selected_posts = {}
    for company in TARGET_COMPANIES:
        company_posts = post_stats[post_stats['company_name'] == company].copy()
        if company_posts.empty:
            LOGGER.warning(f"No posts found for company: {company}")
            continue

        # Prefer posts with 50-250 comments, prioritizing higher depth
        ideal_range = company_posts[
            (company_posts['comment_count'] >= 50) & (company_posts['comment_count'] <= 250)
        ].sort_values(by='max_depth', ascending=False)

        if not ideal_range.empty:
            selected_id = ideal_range.iloc[0]['source_post_id']
            LOGGER.info(f"Selected for {company}: {selected_id} (count={ideal_range.iloc[0]['comment_count']}, depth={ideal_range.iloc[0]['max_depth']}) - Ideal range")
        else:
            # Fallback: find post closest to 100 comments
            company_posts['dist_from_100'] = abs(company_posts['comment_count'] - 100)
            fallback = company_posts.sort_values(by='dist_from_100').iloc[0]
            selected_id = fallback['source_post_id']
            LOGGER.info(f"Selected for {company}: {selected_id} (count={fallback['comment_count']}, depth={fallback['max_depth']}) - Fallback (closest to 100)")

        selected_posts[company] = selected_id

    return selected_posts


def plot_single_post_graph(
    grp: pd.DataFrame,
    target_post_id: str,
    output_dir: Path
) -> None:
    """Builds graph for a single post's comments, adds a source post node, and saves plot."""

    if grp.empty:
        LOGGER.warning("Skipping empty group for post_id: %s", target_post_id)
        return

    LOGGER.info(f"Building graph for {target_post_id} ({len(grp)} comments)...")
    G = nx.DiGraph()
    grp_dict = grp.set_index('id').to_dict(orient='index')

    # Add comment nodes and reply edges
    for node_id, data in grp_dict.items():
        G.add_node(node_id, depth=data.get('depth', 0)) # Store depth if needed
        pid = data.get("parent_id")
        if pd.notna(pid) and pid != '' and pid in grp_dict:
            G.add_edge(pid, node_id)
        elif isinstance(pid, str) and pid.lower() == 'nan':
            pass # Treat as root

    # --- Add artificial source post node --- 
    source_node_id = "SOURCE_POST"
    G.add_node(source_node_id, depth=-1) # Assign artificial depth for potential styling

    # Identify original root comments (no parent comment)
    original_roots = [n for n, d in G.in_degree() if d == 0 and n != source_node_id]

    # Add edges from source post node to original root comments
    for root in original_roots:
        G.add_edge(source_node_id, root)
    # ------------------------------------------ 

    # Node coloring: Distinguish Source Post, Original Roots, Replies
    node_colors = []
    for node in G.nodes():
        if node == source_node_id:
            node_colors.append('black') # Source Post node color
        elif node in original_roots:
            node_colors.append('red')   # Original root comment color
        else:
            node_colors.append('lightblue') # Reply comment color

    # Basic plotting setup
    plt.figure(figsize=(18, 18))

    # --- Layout attempt (no PATH modification) --- 
    pos = None
    try:
        import pydot
        # Rely on pydot finding dot.exe in the system PATH
        pos = nx.nx_pydot.graphviz_layout(G, prog='dot')
        LOGGER.info("Using pydot 'dot' layout.")
    except ImportError:
         LOGGER.warning("pydot not found. Cannot attempt dot layout.")
    except Exception as e:
        # Catch potential errors if dot is not found in PATH or other layout issues
        LOGGER.warning(f"Graphviz layout via pydot failed (is Graphviz installed and in PATH? Error: {e}), falling back to spring layout.")

    # Fallback layout if dot layout failed
    if pos is None:
        LOGGER.info("Using fallback spring layout.")
        pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Drawing logic (remains the same)
    nx.draw(
        G,
        pos,
        with_labels=False,
        node_size=40,
        node_color=node_colors,
        arrowsize=5,
        alpha=0.7,
        width=0.4,
    )

    # Saving logic (remains the same)
    safe_filename = target_post_id.replace('__', '_').replace(' ', '_').replace(':', '-')
    plt.title(f"Comment Graph: {target_post_id}", fontsize=12)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = output_dir / f"{safe_filename}_graph.png"
    try:
        plt.savefig(output_filename, dpi=300, bbox_inches="tight")
        LOGGER.info("Graph saved to %s", output_filename)
    except Exception as e:
        LOGGER.error("Failed to save plot for %s: %s", target_post_id, e)
    finally:
        plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate visualizations for representative comment graphs from each company."
    )
    # Removed target_post_id argument
    parser.add_argument(
        "input_csv_path",
        type=Path,
        help="Path to the CSV file containing comments and graph features (e.g., data/derived/graphed_comments.csv)",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to save the output graph PNG images (e.g., results/figures)",
    )
    args = parser.parse_args()

    LOGGER.info("Loading data from %s", args.input_csv_path)
    if not args.input_csv_path.exists():
        LOGGER.error("Input file not found: %s", args.input_csv_path)
        return
    try:
        df = pd.read_csv(args.input_csv_path)
    except Exception as e:
        LOGGER.error("Failed to read CSV: %s", e)
        return

    # Select representative posts
    selected_posts = select_representative_posts(df)

    if not selected_posts:
        LOGGER.error("No representative posts could be selected. Exiting.")
        return

    # Plot graph for each selected post
    for company, post_id in selected_posts.items():
        LOGGER.info(f"--- Processing selected post for {company}: {post_id} ---")
        grp = df[df["source_post_id"] == post_id].copy()
        plot_single_post_graph(grp, post_id, args.output_dir)

    LOGGER.info("Processing complete.")

if __name__ == "__main__":
    main() 