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
    """Return *df* with four additional graph‑based features.

    The computation is performed per *source post* (one brand post on
    Facebook).  A surrogate column ``source_post_id`` is created by
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
        Original dataframe with the columns ``root_id``, ``depth``,
        ``sibling_count``, and ``time_since_root`` appended.
    """

    required = {"id", "parent_id", "comment_date", "company_name", "post_date"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Input data is missing required column(s): {missing}")

    # ensure datetime
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
        for _, row in grp.iterrows():
            G.add_node(row["id"], comment_date=row["comment_date"])
            pid = row["parent_id"]
            if pd.notna(pid) and pid in grp["id"].values:
                G.add_edge(pid, row["id"])

        # Identify roots (top‑level comments without in‑edges)
        roots = [n for n in G.nodes if G.in_degree(n) == 0]

        # pre‑compute shortest path length and root for every node
        features = {}
        for root in roots:
            try:
                lengths = nx.single_source_shortest_path_length(G, root)
            except nx.NetworkXError:
                continue

            root_time = G.nodes[root]["comment_date"]
            for node, depth in lengths.items():
                # skip if already filled (a node may belong to multiple
                # disconnected roots in pathological data; keep shallowest)
                if node in features and depth >= features[node]["depth"]:
                    continue

                sibling_count = (
                    len(list(G.successors(list(G.predecessors(node))[0]))) - 1
                    if G.in_degree(node) == 1
                    else len(roots) - 1
                )

                # time delta
                node_time = G.nodes[node]["comment_date"]
                tsr = (
                    (node_time - root_time).floor("s")  # ensure Timedelta[ns]
                    if pd.notna(node_time) and pd.notna(root_time)
                    else pd.NaT
                )

                features[node] = {
                    "root_id": root,
                    "depth": depth,
                    "sibling_count": sibling_count,
                    "time_since_root": tsr,
                }

        # any isolated nodes not in *roots*?
        for n in G.nodes:
            if n not in features:
                features[n] = {
                    "root_id": n,
                    "depth": 0,
                    "sibling_count": len(roots) - 1,
                    "time_since_root": pd.Timedelta(0),
                }

        feature_frames.append(pd.DataFrame.from_dict(features, orient="index"))

    if not feature_frames:
        LOGGER.warning("No graph features were generated; returning original df.")
        return df

    feature_df = pd.concat(feature_frames).reset_index().rename(columns={"index": "id"})
    out = df.merge(feature_df, on="id", how="left")

    # final type assurance
    out["depth"] = out["depth"].fillna(0).astype("Int64")
    out["sibling_count"] = out["sibling_count"].fillna(0).astype("Int64")
    out.loc[out["depth"] == 0, "time_since_root"] = out.loc[
        out["depth"] == 0, "time_since_root"
    ].fillna(pd.Timedelta(0))

    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Add conversational graph features to comments.")
    ap.add_argument("input", help="CSV or Parquet file with raw Facebook comments")
    ap.add_argument("output", help="Destination CSV or Parquet file")
    return ap.parse_args()


def _read_any(path: Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("Only .csv or .parquet files are supported.")


def _write_any(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    if path.suffix == ".csv":
        df.to_csv(path, index=False)
    elif path.suffix in {".parquet", ".pq"}:
        df.to_parquet(path, index=False)
    else:
        raise ValueError("Only .csv or .parquet outputs are supported.")


def main() -> None:
    args = _parse_args()
    LOGGER.info("Loading %s", args.input)
    df = _read_any(args.input)

    LOGGER.info("Calculating graph features…")
    df_out = calculate_graph_features(df)

    LOGGER.info("Writing %s", args.output)
    _write_any(df_out, args.output)
    LOGGER.info("Done.")


if __name__ == "__main__":
    main()
