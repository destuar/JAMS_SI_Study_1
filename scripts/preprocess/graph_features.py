"""graph_features.py

Compute conversational-thread graph features for Facebook comment data.

Columns expected
----------------
id             : unique comment identifier (string)
parent_id      : identifier of parent comment; NaN / '' if root
comment_date   : ISO date or datetime string
company_name   : retailer name
post_date      : original Facebook post timestamp

The script adds for every comment:
- root_id         : id of the root (top‑level) comment in the thread
- depth           : number of edges from root to the comment (root = 0)
- sibling_count   : other comments that share the same direct parent
- time_since_root : pandas Timedelta between this comment and its root

Usage
-----
python graph_features.py in.csv out.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import networkx as nx
import pandas as pd

# Define expected output columns structure
FEATURE_COLS = ['id', 'root_id', 'depth', 'sibling_count', 'time_since_root']

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# --------------------------------------------------------------------------- #
# Core routine
# --------------------------------------------------------------------------- #


def calculate_graph_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with id and four graph‑based features.

    The computation is performed per *source post* (one brand post on
    Facebook). A surrogate column ``source_post_id`` is created by
    concatenating ``company_name`` and ``post_date``; adjust if your raw
    dataset already contains a canonical post id.

    Parameters
    ----------
    df : DataFrame
        Must contain at least::

            id, parent_id, comment_date, company_name, post_date

    Returns
    -------
    DataFrame
        DataFrame with columns: id, root_id, depth,
        sibling_count, and time_since_root.
    """

    required = {"id", "parent_id", "comment_date", "company_name", "post_date"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Input data is missing required column(s): {missing}")

    # ensure datetime
    # Use copy to avoid SettingWithCopyWarning if df is a slice
    df = df.copy()
    df["comment_date"] = pd.to_datetime(df["comment_date"], errors="coerce")
    df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce")

    # build grouping key
    df["source_post_id"] = (
        df["company_name"].astype(str) + "__" + df["post_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    )

    feature_frames: list[pd.DataFrame] = []

    # iterate over each post
    for post_id, grp in df.groupby("source_post_id", sort=False):
        LOGGER.info("Processing post %s with %d comments", post_id, len(grp))

        # build directed graph parent -> child
        G = nx.DiGraph()
        grp_dict = grp.set_index('id').to_dict(orient='index') # Faster lookups

        for node_id, data in grp_dict.items():
            G.add_node(node_id, comment_date=data["comment_date"])
            pid = data["parent_id"]
            # Check if parent_id is valid and exists within the current group
            if pd.notna(pid) and pid != '' and pid in grp_dict:
                G.add_edge(pid, node_id)
            # Handle cases where parent_id might be float NaN converted to string 'nan'
            elif isinstance(pid, str) and pid.lower() == 'nan':
                pass # Treat as root
            elif pid == node_id:
                 LOGGER.warning(f"Comment {node_id} lists itself as parent in post {post_id}. Treating as root.")

        # Identify roots (nodes with in-degree 0)
        roots = [n for n, d in G.in_degree() if d == 0]

        # pre‑compute shortest path length and root for every node
        features = {}
        processed_nodes = set()

        for root in roots:
            try:
                # Use BFS for path lengths and nodes reachable from this root
                lengths = nx.single_source_shortest_path_length(G, root)
                reachable_nodes = set(lengths.keys())
            except nx.NetworkXError as e:
                 LOGGER.error(f"NetworkX error processing root {root} in post {post_id}: {e}")
                 continue # Skip this root if error occurs

            root_time = G.nodes[root]["comment_date"]

            for node in reachable_nodes:
                # Skip if already processed from a shorter path via another root (unlikely but possible)
                if node in processed_nodes:
                    continue

                depth = lengths[node]
                node_time = G.nodes[node]["comment_date"]

                # Calculate sibling count
                predecessors = list(G.predecessors(node))
                if predecessors:
                     parent = predecessors[0] # Assuming single parent from BFS path
                     siblings = list(G.successors(parent))
                     sibling_count = len(siblings) - 1 # Exclude self
                else: # Node is a root
                     # Siblings are other roots in the same post
                     sibling_count = len(roots) - 1

                # Calculate time_since_root, handling NaT
                tsr = pd.NaT
                if pd.notna(node_time) and pd.notna(root_time):
                    # Calculate time difference
                    time_diff = node_time - root_time
                    # Ensure non-negative time difference, floor to seconds
                    tsr = max(time_diff, pd.Timedelta(seconds=0)).floor('s')
                # If node is root, time_since_root should be 0 unless its date is NaT
                if node == root and pd.notna(root_time):
                    tsr = pd.Timedelta(seconds=0)
                # If node == root and root_time is NaT, tsr remains NaT (handled above)

                features[node] = {
                    "root_id": root,
                    "depth": depth,
                    "sibling_count": sibling_count,
                    "time_since_root": tsr,
                }
                processed_nodes.add(node)

        # Handle nodes potentially missed if graph was disconnected or errors occurred
        missed_nodes = set(G.nodes()) - processed_nodes
        if missed_nodes:
             LOGGER.warning(f"Post {post_id}: {len(missed_nodes)} nodes were not reached from identified roots. Treating as isolated roots.")
             for node in missed_nodes:
                 node_time = G.nodes[node]["comment_date"]
                 features[node] = {
                     "root_id": node,
                     "depth": 0,
                     "sibling_count": len(roots) -1 + len(missed_nodes) -1 , # Other roots + other missed nodes
                     "time_since_root": pd.Timedelta(seconds=0) if pd.notna(node_time) else pd.NaT,
                 }

        if features: # Only append if features were generated for this group
             feature_frames.append(pd.DataFrame.from_dict(features, orient='index'))

    # Handle case where no features were generated at all
    if not feature_frames:
        LOGGER.warning("No graph features were generated across any posts.")
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(columns=FEATURE_COLS)

    # Concatenate features from all groups
    feature_df = pd.concat(feature_frames)
    feature_df = feature_df.reset_index().rename(columns={"index": "id"})

    # Ensure correct column order and types before returning
    feature_df = feature_df[FEATURE_COLS] # Select and order columns

    feature_df['depth'] = feature_df['depth'].astype('Int64')
    feature_df['sibling_count'] = feature_df['sibling_count'].astype('Int64')
    # Do not fillna time_since_root with 0 globally, only for depth==0 where date is not NaT
    # Already handled during feature calculation.

    # Check for any remaining NaNs in essential feature columns (shouldn't happen)
    if feature_df[[f for f in FEATURE_COLS if f != 'time_since_root']].isnull().any().any():
        LOGGER.warning("NaN values found in feature columns after processing. Check logic.")

    return feature_df


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Add conversational graph features to comments.")
    ap.add_argument("input", help="CSV or Parquet file with raw Facebook comments")
    ap.add_argument("output", help="Destination CSV or Parquet file for merged data")
    return ap.parse_args()


def _read_any(path: Path | str) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Only .csv or .parquet files are supported.")


def _write_any(df: pd.DataFrame, path: Path | str) -> None:
    path = Path(path)
    if path.suffix == ".csv":
        df.to_csv(path, index=False)
    elif path.suffix in {".parquet", ".pq"}:
        df.to_parquet(path, index=False)
    else:
        raise ValueError("Only .csv or .parquet outputs are supported.")


def main() -> None:
    args = _parse_args()
    LOGGER.info("Loading input data from %s", args.input)
    df_input = _read_any(args.input)

    # Keep original columns for merging later
    original_cols = df_input.columns.tolist()

    LOGGER.info("Calculating graph features…")
    # Get only the feature DataFrame
    feature_df = calculate_graph_features(df_input)

    LOGGER.info("Merging features back into original data...")
    # Ensure feature_df doesn't contain columns already in df_input except 'id'
    cols_to_merge = [col for col in feature_df.columns if col != 'id']
    merged_df = pd.merge(df_input, feature_df[['id'] + cols_to_merge], on='id', how='left')

    # Optional: Check if merge introduced NaNs in feature columns unexpectedly
    # This might happen if an ID existed in df_input but not feature_df (shouldn't happen with current logic)
    if merged_df[cols_to_merge].isnull().any().any():
         LOGGER.warning("NaN values found in feature columns after merge. Check IDs.")
         # Fill potentially introduced NaNs in numerical features if necessary, e.g.:
         # merged_df['depth'] = merged_df['depth'].fillna(0).astype('Int64')
         # merged_df['sibling_count'] = merged_df['sibling_count'].fillna(0).astype('Int64')

    LOGGER.info("Writing merged data with features to %s (%d rows)", args.output, len(merged_df))
    _write_any(merged_df, args.output)
    LOGGER.info("Done.")


if __name__ == "__main__":
    main()
