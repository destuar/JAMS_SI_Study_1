import pandas as pd
import networkx as nx
from datetime import datetime
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_graph_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates graph-based features (root_id, depth, sibling_count, time_since_root)
    for each comment within its conversation thread using NetworkX.

    Args:
        df: DataFrame containing comments with columns like 'id', 'parent_id',
            'comment_date', and a column identifying the original post (e.g., 'post_id' or 'company_name' + 'post_date').

    Returns:
        DataFrame with added columns: 'root_id', 'depth', 'sibling_count', 'time_since_root'.
    """
    # Ensure necessary columns are present
    required_cols = ['id', 'parent_id', 'comment_date'] # Add post identifier column if needed
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input DataFrame must contain columns: {required_cols}")

    # Convert comment_date to datetime objects if not already
    if not pd.api.types.is_datetime64_any_dtype(df['comment_date']):
         # Assuming 'comment_date' is parsable; add error handling as needed
        df['comment_date'] = pd.to_datetime(df['comment_date'], errors='coerce')

    # Placeholder for the unique identifier of the source post
    # We need to group comments by post before building the graph.
    # Assuming a column like 'source_post_id' exists or can be constructed.
    # If not, we need to adapt this logic.
    post_group_col = 'source_post_id' # Replace with actual column name
    if post_group_col not in df.columns:
        # Attempt to create a unique identifier if possible, e.g., from company and post_date
        if 'company_name' in df.columns and 'post_date' in df.columns:
             logging.info("Creating 'source_post_id' from 'company_name' and 'post_date'.")
             df[post_group_col] = df['company_name'].astype(str) + "_" + df['post_date'].astype(str)
        else:
            raise ValueError(f"Column '{post_group_col}' not found, and cannot be constructed from 'company_name' and 'post_date'. Please provide a column identifying the source post for each comment.")


    all_features = []

    # Process comments group by group (one group per original Facebook post)
    for post_id, group in df.groupby(post_group_col):
        logging.info(f"Processing post group: {post_id} ({len(group)} comments)")
        G = nx.DiGraph()
        nodes = {}
        edges = []
        root_nodes = []

        # Add nodes and prepare edges
        for _, row in group.iterrows():
            nodes[row['id']] = {'data': row.to_dict()}
            # Check for NaN/NaT or empty string in parent_id values indicating a root comment
            # Handle potential float NaNs if the column was mixed-type before becoming object/string
            is_root = pd.isna(row['parent_id']) or row['parent_id'] == '' or str(row['parent_id']).lower() == 'nan'
            if is_root:
                 root_nodes.append(row['id'])
            else:
                # Add edge if parent exists in the current group
                if row['parent_id'] in group['id'].values:
                    edges.append((row['parent_id'], row['id']))
                else:
                    # Parent ID exists but is not in the current group (edge case, treat as root)
                    # This might happen if parent comment was deleted or not scraped
                    logging.warning(f"Comment {row['id']} has parent {row['parent_id']} not found in group {post_id}. Treating as root.")
                    root_nodes.append(row['id'])


        G.add_nodes_from(nodes.items())
        G.add_edges_from(edges)

        # Calculate features for this group's graph
        post_features = {}
        for node_id in G.nodes():
            node_data = G.nodes[node_id]['data']
            node_attrs = {'id': node_id} # Start with the node ID itself

            # Find root and depth
            current_root_id = None
            current_depth = 0
            try:
                 # Find the ultimate ancestor (root) by traversing upwards
                 # This is complex in DiGraph; simpler to use descendants from known roots.
                 # We will iterate through roots and find descendants instead.
                 pass # Placeholder - logic moved below
            except nx.NetworkXError:
                 logging.warning(f"Error processing paths for node {node_id} in post {post_id}.")
                 node_attrs['root_id'] = node_id # Default to self if error
                 node_attrs['depth'] = 0


            # Calculate sibling count (nodes with the same immediate predecessor)
            predecessors = list(G.predecessors(node_id))
            if predecessors:
                 parent_id = predecessors[0] # Assuming single parent
                 siblings = list(G.successors(parent_id))
                 node_attrs['sibling_count'] = len(siblings) - 1 # Exclude self
            else:
                 # Root node or orphaned node
                 node_attrs['sibling_count'] = len([rn for rn in root_nodes if rn != node_id and list(G.predecessors(rn)) == []]) # Siblings are other roots in this context


            # Placeholder for time_since_root calculation
            node_attrs['time_since_root'] = pd.NaT # Needs root info first

            post_features[node_id] = node_attrs

        # Iterate through roots to calculate depth and root_id correctly
        for root_id in root_nodes:
             if root_id not in post_features: continue # Skip if root wasn't in the main graph nodes for some reason
             post_features[root_id].update({'root_id': root_id, 'depth': 0, 'time_since_root': pd.Timedelta(seconds=0)})
             root_time = G.nodes[root_id]['data']['comment_date']

             # Use BFS or DFS to find descendants and calculate depth/time
             for target_id in nx.bfs_nodes(G, source=root_id):
                 if target_id == root_id: continue # Skip root itself

                 # Check if target_id is reachable (should be if bfs_nodes returns it)
                 if nx.has_path(G, root_id, target_id):
                      path_len = nx.shortest_path_length(G, source=root_id, target=target_id)
                      target_time = G.nodes[target_id]['data']['comment_date']

                      # Update features if this path is valid
                      if target_id in post_features:
                           post_features[target_id].update({
                               'root_id': root_id,
                               'depth': path_len
                           })
                           # Calculate time difference if times are valid
                           if pd.notna(root_time) and pd.notna(target_time):
                               time_diff = target_time - root_time
                               # Ensure non-negative time difference
                               post_features[target_id]['time_since_root'] = max(time_diff, pd.Timedelta(seconds=0))
                           else:
                               post_features[target_id]['time_since_root'] = pd.NaT
                      else:
                           logging.warning(f"Node {target_id} found in BFS but not in post_features for post {post_id}.")

        # Convert features dict to DataFrame and append
        group_features_df = pd.DataFrame.from_dict(post_features, orient='index')
        all_features.append(group_features_df)

    # Combine features from all groups
    if not all_features:
         logging.warning("No features were calculated. Returning original DataFrame.")
         # Add empty columns if expected
         df['root_id'] = None
         df['depth'] = pd.NA
         df['sibling_count'] = pd.NA
         df['time_since_root'] = pd.NaT
         return df

    features_df = pd.concat(all_features)

    # Merge features back into the original DataFrame
    # Ensure index is suitable for merging, or use 'id' column
    df_with_features = df.merge(features_df, on='id', how='left')

    # Fill NA for nodes that might not have been processed (e.g., isolated nodes not in roots/descendants)
    df_with_features['depth'] = df_with_features['depth'].fillna(0).astype(int) # Default depth 0 if NA
    df_with_features['sibling_count'] = df_with_features['sibling_count'].fillna(0).astype(int) # Default siblings 0 if NA
    # root_id might be missing if a node was disconnected; fill with its own id
    df_with_features['root_id'] = df_with_features['root_id'].fillna(df_with_features['id'])


    return df_with_features

def main():
    parser = argparse.ArgumentParser(description="Calculate comment graph features using NetworkX.")
    parser.add_argument("input_file", help="Path to the input Parquet/CSV file containing comments.")
    parser.add_argument("output_file", help="Path to save the output Parquet/CSV file with added graph features.")
    # Optional: Add argument for the post identifier column if needed
    # parser.add_argument("--post_id_col", default="source_post_id", help="Column name identifying the source post.")

    args = parser.parse_args()

    logging.info(f"Loading data from: {args.input_file}")
    # Load data (add handling for CSV if necessary)
    if args.input_file.endswith('.parquet'):
        df = pd.read_parquet(args.input_file)
    elif args.input_file.endswith('.csv'):
        df = pd.read_csv(args.input_file)
    else:
        raise ValueError("Input file must be .parquet or .csv")

    logging.info("Calculating graph features...")
    df_with_features = calculate_graph_features(df)

    logging.info(f"Saving results to: {args.output_file}")
    # Save results (add handling for CSV if necessary)
    if args.output_file.endswith('.parquet'):
        df_with_features.to_parquet(args.output_file, index=False)
    elif args.output_file.endswith('.csv'):
        df_with_features.to_csv(args.output_file, index=False)
    else:
        raise ValueError("Output file must be .parquet or .csv")

    logging.info("Processing complete.")

if __name__ == "__main__":
    main() 