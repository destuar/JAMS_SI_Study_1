import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
from datetime import datetime # Added for DEI_CUTOFF_DATES

# --- Configuration ---
DATA_FILE = "data/derived/comments_with_sentiment.csv"
TABLES_DIR = "results/tables"
FIGURES_DIR = "results/figures" # As per README structure

# Mappings for labels
STANCE_MAP = {-1: "Anti-DEI", 0: "Neutral-DEI", 1: "Pro-DEI"}
PI_MAP = {-1: "Boycott", 0: "Neutral-PI", 1: "Buy"}
RELEVANCE_MAP = {0: "Not DEI-Relevant", 1: "DEI-Relevant"}

# Color Scheme (Publication Style: Red/Gray/Blue Diverging)
# Using common hex codes for better consistency
COLOR_MAP = {
    "Anti-DEI": "#d62728",    # Red
    "Neutral-DEI": "#cccccc",  # Light Gray
    "Pro-DEI": "#1f77b4",     # Blue
    "Boycott": "#d62728",    # Red
    "Neutral-PI": "#cccccc",  # Light Gray
    "Buy": "#1f77b4",     # Blue
    "Not DEI-Relevant": "#aec7e8", # Light Blue
    "DEI-Relevant": "#1f77b4",    # Darker Blue
    # Add other categories if needed, e.g., for Initial Comment/Reply
    "Initial Comment": "#ff7f0e", # Orange
    "Reply": "#2ca02c"       # Green
}

# Actual label column names from CSV
ACTUAL_STANCE_LABEL_COL = 'gpt4o_pred_stance_label'
ACTUAL_PI_LABEL_COL = 'gpt4o_pred_pi_label'

# Define DEI Cutoff Dates (Announcement Dates)
DEI_CUTOFF_DATES = {
    'Costco': datetime(2025, 1, 23),
    'Delta': datetime(2025, 2, 4),
    'Google': datetime(2025, 2, 5),
    'Target': datetime(2025, 1, 24),
}

def create_output_dirs():
    """Creates output directories if they don't exist."""
    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

def get_announcement_date(df_company_ignored, company_name_for_lookup):
    """Identifies the announcement date for a company from the DEI_CUTOFF_DATES map."""
    # df_company_ignored is no longer used but kept for signature consistency if called elsewhere.
    # The primary input is now company_name_for_lookup.
    return DEI_CUTOFF_DATES.get(company_name_for_lookup) # Returns None if company_name not in map

def plot_counts(df_counts, title, filename, kind='bar', xlabel=None):
    """Helper function to plot and save count data."""
    if df_counts.empty:
        print(f"Skipping plot {filename} as data is empty.")
        return
    
    # Use specified colors if index aligns with COLOR_MAP keys
    colors = [COLOR_MAP.get(cat, '#808080') for cat in df_counts.index] # Default mid-gray if category not in map
    if isinstance(df_counts, pd.Series):
        # Reindex series according to COLOR_MAP order if possible
        ordered_index = [k for k in COLOR_MAP.keys() if k in df_counts.index] 
        # Fallback if no keys match or only one category
        if not ordered_index or len(ordered_index) != len(df_counts.index):
            ordered_index = df_counts.index 
        
        df_counts = df_counts.reindex(ordered_index, fill_value=0)
        colors = [COLOR_MAP.get(cat, '#808080') for cat in df_counts.index] # Recalculate colors after reindex
        ax = df_counts.plot(kind=kind, figsize=(10, 6), color=colors)
    elif isinstance(df_counts, pd.DataFrame):
        # For grouped bar charts (e.g., per company), apply colors per category if possible
        # Ensure columns are ordered according to COLOR_MAP for consistent coloring
        ordered_columns = [k for k in COLOR_MAP.keys() if k in df_counts.columns]
        # Fallback if no keys match or columns dont match categories
        if not ordered_columns or len(ordered_columns) != len(df_counts.columns):
            ordered_columns = df_counts.columns
        df_counts = df_counts.reindex(columns=ordered_columns, fill_value=0) 
        try:
            # Use the COLOR_MAP directly if column names match keys
            mapped_colors = [COLOR_MAP.get(col, '#808080') for col in df_counts.columns] 
            print(f"Applying colors for {filename}: {list(zip(df_counts.columns, mapped_colors))}") # Debug print
            ax = df_counts.plot(kind=kind, figsize=(12, 7), color=mapped_colors)
        except Exception as e:
            print(f"Warning: Could not apply custom colors to grouped bar chart {filename}. Error: {e}")
            ax = df_counts.plot(kind=kind, figsize=(12, 7)) # Fallback

    plt.title(title, fontsize=14)
    plt.ylabel("Number of Comments", fontsize=12)
    plt.xlabel(xlabel if xlabel else "", fontsize=12) # Use provided xlabel or default to none
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Add data labels for bar charts
    if kind == 'bar':
        if isinstance(df_counts, pd.Series):
            for i, v in enumerate(df_counts):
                ax.text(i, v + (df_counts.max() * 0.01), str(int(v)), ha='center', va='bottom', fontsize=10)
        elif isinstance(df_counts, pd.DataFrame):
            # Adding labels to grouped/stacked bars is complex, skipping
            pass

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), dpi=300) # Higher DPI for publication
    plt.close()

def eda_main():
    """Main function to run all EDA steps."""
    # Set seaborn style for aesthetics
    sns.set_style("whitegrid")
    plt.rcParams['figure.facecolor'] = 'white' # Ensure plots don't have transparent background
    plt.rcParams['savefig.facecolor'] = 'white'

    create_output_dirs()

    # --- Load and Prepare Data ---
    print(f"Loading data from {DATA_FILE}...")
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_FILE}. Please ensure the path is correct.")
        return
    
    print("Data loaded. Basic info:")
    df.info()
    print(f"\nShape: {df.shape}")

    # Convert comment_date and post_date to datetime
    date_cols = ['comment_date', 'post_date']
    for col in date_cols:
        if col not in df.columns:
            print(f"Error: '{col}' column not found. Please check the CSV file.")
            # Decide if to return or continue if one is missing, for now, let's be strict for post_date in volume analysis
            if col == 'post_date': 
                print("post_date is crucial for volume analysis by post date. Exiting.")
                return 
            # If only comment_date is missing but post_date exists, some analyses might still run
            # but for now, let's keep it simple or allow continuation with warnings.
        else:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df.dropna(subset=[col], inplace=True) # Drop rows where essential dates are NaT
    
    # Map labels for readability if columns exist
    if ACTUAL_STANCE_LABEL_COL in df.columns:
        df['stance_category'] = df[ACTUAL_STANCE_LABEL_COL].map(STANCE_MAP)
    else:
        print(f"Warning: Column '{ACTUAL_STANCE_LABEL_COL}' not found. Skipping stance-related analyses.")
    
    if ACTUAL_PI_LABEL_COL in df.columns:
        df['pi_category'] = df[ACTUAL_PI_LABEL_COL].map(PI_MAP)
    else:
        print(f"Warning: Column '{ACTUAL_PI_LABEL_COL}' not found. Skipping PI-related analyses.")

    if 'relevance' in df.columns:
        df['relevance_category'] = df['relevance'].map(RELEVANCE_MAP)
    else:
        print("Warning: 'relevance' column not found. Skipping relevance-specific analyses.")

    # --- 1. Stance and Purchase Intention Counts ---
    print("\n--- EDA: Label Counts ---")
    if 'stance_category' in df.columns:
        # Total stance counts
        stance_counts_total = df['stance_category'].value_counts().sort_index()
        print("\nTotal Stance (DEI) Counts:\n", stance_counts_total)
        if not stance_counts_total.empty:
            # Reindex ensures consistent order for plotting and colors
            stance_counts_total = stance_counts_total.reindex(STANCE_MAP.values(), fill_value=0) 
            stance_counts_total.to_csv(os.path.join(TABLES_DIR, "stance_counts_total.csv"))
            plot_counts(stance_counts_total, "Total DEI Stance Counts", "stance_counts_total.png")

        # Per-company stance counts
        stance_counts_company = df.groupby('company_name')['stance_category'].value_counts().unstack(fill_value=0).sort_index()
        print("\nStance (DEI) Counts per Company:\n", stance_counts_company)
        if not stance_counts_company.empty:
            # Reindex columns ensures consistent order for plotting and colors
            stance_counts_company = stance_counts_company.reindex(columns=STANCE_MAP.values(), fill_value=0)
            stance_counts_company.to_csv(os.path.join(TABLES_DIR, "stance_counts_by_company.csv"))
            plot_counts(stance_counts_company, "DEI Stance Counts per Company", "stance_counts_by_company.png")

    if 'pi_category' in df.columns:
        # Total PI counts
        pi_counts_total = df['pi_category'].value_counts().sort_index()
        print("\nTotal Purchase Intention Counts:\n", pi_counts_total)
        if not pi_counts_total.empty:
            # Reindex ensures consistent order for plotting and colors
            pi_counts_total = pi_counts_total.reindex(PI_MAP.values(), fill_value=0) 
            pi_counts_total.to_csv(os.path.join(TABLES_DIR, "pi_counts_total.csv"))
            plot_counts(pi_counts_total, "Total Purchase Intention Counts", "pi_counts_total.png")

        # Per-company PI counts
        pi_counts_company = df.groupby('company_name')['pi_category'].value_counts().unstack(fill_value=0).sort_index()
        print("\nPurchase Intention Counts per Company:\n", pi_counts_company)
        if not pi_counts_company.empty:
            # Reindex columns ensures consistent order for plotting and colors
            pi_counts_company = pi_counts_company.reindex(columns=PI_MAP.values(), fill_value=0)
            pi_counts_company.to_csv(os.path.join(TABLES_DIR, "pi_counts_by_company.csv"))
            plot_counts(pi_counts_company, "Purchase Intention Counts per Company", "pi_counts_by_company.png")

    # --- 2. Time Series Trends ---
    print("\n--- EDA: Time Series Trends (Plots Removed as Requested) ---")
    # --- Plots Removed ---
    # Original code for plotting weekly averages and proportions is removed or commented out below
    # We still calculate the data for potential use in tables if needed.

    if 'comment_date' in df.columns and 'company_name' in df.columns and 'before_DEI' in df.columns:
        df_sorted = df.sort_values('comment_date')
        
        for label_col, cat_col, label_map, name_prefix in [
            (ACTUAL_STANCE_LABEL_COL, 'stance_category', STANCE_MAP, "DEI_Stance"),
            (ACTUAL_PI_LABEL_COL, 'pi_category', PI_MAP, "Purchase_Intention")
        ]:
            if label_col not in df.columns or cat_col not in df.columns:
                print(f"Skipping time series table generation for {name_prefix} due to missing columns.")
                continue

            # Calculate weekly average data (for tables)
            df_weekly_avg = df_sorted.groupby(['company_name', 'before_DEI', pd.Grouper(key='comment_date', freq='W')])[label_col].agg(['mean', 'count']).reset_index()
            if not df_weekly_avg.empty:
                df_weekly_avg.to_csv(os.path.join(TABLES_DIR, f"weekly_avg_{name_prefix.lower()}.csv"), index=False)
                print(f"Saved table: weekly_avg_{name_prefix.lower()}.csv")
            
            # Calculate weekly proportion data (for tables)
            df_weekly_props = df_sorted.groupby(['company_name', 'before_DEI', pd.Grouper(key='comment_date', freq='W')])[cat_col].value_counts(normalize=True).unstack(fill_value=0).reset_index()
            if not df_weekly_props.empty:
                df_weekly_props.to_csv(os.path.join(TABLES_DIR, f"weekly_proportions_{name_prefix.lower()}.csv"), index=False)
                print(f"Saved table: weekly_proportions_{name_prefix.lower()}.csv")

    else:
        print("Skipping time series table generation due to missing columns: 'comment_date', 'company_name', or 'before_DEI'.")


    # --- 3. Additional EDA ---
    print("\n--- EDA: Additional Analyses ---")

    # a. Distribution of Comment Volume Over Time (by post_date)
    if 'id' in df.columns and 'post_date' in df.columns: # Assuming 'id' is a unique comment identifier
        comment_volume_by_post = df.groupby(['company_name', pd.Grouper(key='post_date', freq='D')])['id'].count().reset_index(name='comment_count')
        table_filename = "daily_comment_volume_by_post_date.csv"
        comment_volume_by_post.to_csv(os.path.join(TABLES_DIR, table_filename), index=False)
        print(f"Saved table: {table_filename}")

        for company in comment_volume_by_post['company_name'].unique():
            company_volume_df = comment_volume_by_post[comment_volume_by_post['company_name'] == company]
            if company_volume_df.empty: continue
            
            # get_announcement_date uses company name to lookup from DEI_CUTOFF_DATES
            announcement_date = get_announcement_date(None, company) # Pass None for df_company, company name for lookup

            plt.figure(figsize=(12, 6))
            plt.plot(company_volume_df['post_date'], company_volume_df['comment_count'], marker='.', linestyle='-')
            if announcement_date:
                plt.axvline(announcement_date, color='red', linestyle='--', linewidth=1, label=f'Announcement Date ({announcement_date.strftime("%Y-%m-%d")})')
                plt.legend()
            plt.title(f"Daily Comment Volume (by Post Date) for {company}", fontsize=14)
            plt.xlabel("Post Date", fontsize=12)
            plt.ylabel("Number of Comments", fontsize=12)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_DIR, f"daily_comment_volume_by_post_date_{company}.png"), dpi=300)
            plt.close()
    else:
        print("Warning: 'id' or 'post_date' column for comment counting not found. Skipping comment volume by post_date analysis.")


    # b. Interaction between DEI Stance and Purchase Intention
    if 'stance_category' in df.columns and 'pi_category' in df.columns:
        stance_pi_crosstab = pd.crosstab(df['stance_category'], df['pi_category'])
        print("\nCrosstab: DEI Stance vs. Purchase Intention (Counts):\n", stance_pi_crosstab)
        stance_pi_crosstab.to_csv(os.path.join(TABLES_DIR, "stance_pi_crosstab_counts.csv"))

        # Ensure correct order for heatmap based on STANCE_MAP and PI_MAP if possible
        ordered_stance = [STANCE_MAP[key] for key in sorted(STANCE_MAP.keys())]
        ordered_pi = [PI_MAP[key] for key in sorted(PI_MAP.keys())]
        
        stance_pi_crosstab_norm = pd.crosstab(df['stance_category'], df['pi_category'], normalize='index')
        # Reindex to ensure consistent order in heatmap
        stance_pi_crosstab_norm = stance_pi_crosstab_norm.reindex(index=ordered_stance, columns=ordered_pi, fill_value=0)

        print("\nCrosstab: DEI Stance vs. Purchase Intention (Normalized by Stance):\n", stance_pi_crosstab_norm)
        stance_pi_crosstab_norm.to_csv(os.path.join(TABLES_DIR, "stance_pi_crosstab_normalized.csv"))

        # Per company
        for company in df['company_name'].unique():
            company_df = df[df['company_name'] == company]
            if not company_df.empty:
                company_crosstab_norm = pd.crosstab(company_df['stance_category'], company_df['pi_category'], normalize='index')
                company_crosstab_norm = company_crosstab_norm.reindex(index=ordered_stance, columns=ordered_pi, fill_value=0)

                if not company_crosstab_norm.empty:
                    company_crosstab_norm.to_csv(os.path.join(TABLES_DIR, f"stance_pi_crosstab_normalized_{company}.csv"))


    # c. Role of Comment Relevance
    if 'relevance_category' in df.columns and 'stance_category' in df.columns:
        print("\n--- EDA: Relevance Analysis ---")
        relevance_stance_counts = df.groupby('relevance_category')['stance_category'].value_counts().unstack(fill_value=0)
        print("\nDEI Stance Counts by Comment Relevance:\n", relevance_stance_counts)
        relevance_stance_counts.to_csv(os.path.join(TABLES_DIR, "relevance_stance_counts.csv"))
        if not relevance_stance_counts.empty:
            plot_counts(relevance_stance_counts.T, "DEI Stance Counts by Comment Relevance", "relevance_stance_counts.png", kind='bar', xlabel="Comment Relevance")
        
        if 'pi_category' in df.columns:
            relevance_pi_counts = df.groupby('relevance_category')['pi_category'].value_counts().unstack(fill_value=0)
            print("\nPurchase Intention Counts by Comment Relevance:\n", relevance_pi_counts)
            relevance_pi_counts.to_csv(os.path.join(TABLES_DIR, "relevance_pi_counts.csv"))
            if not relevance_pi_counts.empty:
                # Ensure columns are ordered
                relevance_pi_counts = relevance_pi_counts.reindex(columns=PI_MAP.values(), fill_value=0)
                relevance_pi_counts.to_csv(os.path.join(TABLES_DIR, "relevance_pi_counts.csv"))
                plot_counts(relevance_pi_counts.T, "Purchase Intention Counts by Comment Relevance", "relevance_pi_counts.png", kind='bar', xlabel="Comment Relevance")

                # Stance vs PI for DEI-Relevant comments only
                relevant_df = df[(df['relevance'] == 1) & (ACTUAL_STANCE_LABEL_COL in df.columns) & (ACTUAL_PI_LABEL_COL in df.columns)]
                if not relevant_df.empty and 'stance_category' in relevant_df.columns and 'pi_category' in relevant_df.columns:
                    relevant_stance_pi_crosstab_norm = pd.crosstab(relevant_df['stance_category'], relevant_df['pi_category'], normalize='index')
                    relevant_stance_pi_crosstab_norm = relevant_stance_pi_crosstab_norm.reindex(index=ordered_stance, columns=ordered_pi, fill_value=0)
                    
                    print("\nCrosstab (DEI-Relevant Only): DEI Stance vs. PI (Normalized by Stance):\n", relevant_stance_pi_crosstab_norm)
                    relevant_stance_pi_crosstab_norm.to_csv(os.path.join(TABLES_DIR, "relevant_stance_pi_crosstab_normalized.csv"))
                else:
                    print("No DEI-relevant comments or required columns found for stance vs PI interaction analysis.")


    # d. Thread Analysis (Basic) - Requires 'depth'
    if 'depth' in df.columns and 'stance_category' in df.columns:
        print("\n--- EDA: Basic Thread Analysis ---")
        df['comment_type_derived'] = df['depth'].apply(lambda x: 'Initial Comment' if x == 0 else 'Reply')
        thread_stance_counts = df.groupby('comment_type_derived')['stance_category'].value_counts(normalize=True).unstack(fill_value=0)
        # Ensure columns are in the correct order
        thread_stance_counts = thread_stance_counts.reindex(columns=STANCE_MAP.values(), fill_value=0)
        print("\nProportion of DEI Stances by Comment Type (Initial vs. Reply):\n", thread_stance_counts)
        if not thread_stance_counts.empty:
            thread_stance_counts.to_csv(os.path.join(TABLES_DIR, "thread_type_stance_proportions.csv"))
            plot_counts(thread_stance_counts.T, "Proportion of DEI Stances by Comment Type", "thread_type_stance_proportions.png", kind='bar', xlabel="Comment Type")

            if 'pi_category' in df.columns:
                thread_pi_counts = df.groupby('comment_type_derived')['pi_category'].value_counts(normalize=True).unstack(fill_value=0)
                # Ensure columns are in the correct order
                thread_pi_counts = thread_pi_counts.reindex(columns=PI_MAP.values(), fill_value=0)
                print("\nProportion of PI by Comment Type (Initial vs. Reply):\n", thread_pi_counts)
                if not thread_pi_counts.empty:
                    thread_pi_counts.to_csv(os.path.join(TABLES_DIR, "thread_type_pi_proportions.csv"))
                    plot_counts(thread_pi_counts.T, "Proportion of Purchase Intentions by Comment Type", "thread_type_pi_proportions.png", kind='bar', xlabel="Comment Type")


    # e. Reaction Count Analysis
    if 'reaction_count' in df.columns:
        print("\n--- EDA: Reaction Count Analysis ---")
        # Cap reaction count for visualization to handle extreme outliers
        # df['reaction_count_viz'] = df['reaction_count'].clip(upper=df['reaction_count'].quantile(0.99))
        df['reaction_count_viz'] = df['reaction_count']


        if 'stance_category' in df.columns:
            plt.figure(figsize=(10, 6))
            # Use hue for categorization and map palette directly
            order_stance = [s for s in STANCE_MAP.values() if s in df['stance_category'].unique()]
            sns.boxplot(data=df, x='stance_category', y='reaction_count_viz', order=order_stance, hue='stance_category', palette=COLOR_MAP, legend=False)
            plt.title("Distribution of Reaction Counts by DEI Stance", fontsize=14)
            plt.ylabel("Reaction Count (Log Scale)", fontsize=12)
            plt.xlabel("DEI Stance")
            plt.yscale('symlog') # Use symlog for wide range, handles zeros
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_DIR, "reaction_counts_by_stance.png"), dpi=300)
            plt.close()

            avg_reactions_stance = df.groupby('stance_category')['reaction_count'].agg(['mean', 'median', 'count']).sort_values(by='mean', ascending=False)
            print("\nAverage Reaction Counts by DEI Stance:\n", avg_reactions_stance)
            avg_reactions_stance.to_csv(os.path.join(TABLES_DIR, "avg_reactions_by_stance.csv"))

        if 'pi_category' in df.columns:
            plt.figure(figsize=(10, 6))
            order_pi = [p for p in PI_MAP.values() if p in df['pi_category'].unique()]
            # Use hue for categorization and map palette directly
            sns.boxplot(data=df, x='pi_category', y='reaction_count_viz', order=order_pi, hue='pi_category', palette=COLOR_MAP, legend=False)
            plt.title("Distribution of Reaction Counts by Purchase Intention", fontsize=14)
            plt.ylabel("Reaction Count (Log Scale)", fontsize=12)
            plt.xlabel("Purchase Intention")
            plt.yscale('symlog')
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_DIR, "reaction_counts_by_pi.png"), dpi=300)
            plt.close()
            
            avg_reactions_pi = df.groupby('pi_category')['reaction_count'].agg(['mean', 'median', 'count']).sort_values(by='mean', ascending=False)
            print("\nAverage Reaction Counts by Purchase Intention:\n", avg_reactions_pi)
            avg_reactions_pi.to_csv(os.path.join(TABLES_DIR, "avg_reactions_by_pi.csv"))
            
    print("\n--- EDA Script Completed ---")
    print(f"Tables saved to: {TABLES_DIR}")
    print(f"Figures saved to: {FIGURES_DIR}")

if __name__ == "__main__":
    eda_main()
