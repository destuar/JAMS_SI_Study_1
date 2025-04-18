import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Remove sys.path manipulation

# Revert to original import style
from scripts.preprocess.graph_features import calculate_graph_features

@pytest.fixture
def sample_comments_df() -> pd.DataFrame:
    """Creates a sample DataFrame mimicking master_data.csv structure."""
    data = {
        'company_name': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'A'],
        'post_date': [
            '2024-01-01 10:00:00', '2024-01-01 10:00:00', '2024-01-01 10:00:00', # Post A1
            '2024-01-01 10:00:00', '2024-01-01 10:00:00', # Post A1
            '2024-02-15 12:00:00', '2024-02-15 12:00:00', '2024-02-15 12:00:00', # Post B1
            '2024-01-01 10:00:00'  # Post A1 - Orphan
        ],
        'id': ['a1', 'a2', 'a3', 'a4', 'a5', 'b1', 'b2', 'b3', 'a6'],
        'parent_id': ['', 'a1', 'a1', 'a3', '', '', 'b1', 'b4', 'a99'], # a5 is root, b1 is root, b2 replies to b1, b3 replies to b4, a6 is orphaned
        'comment_date': [
            '2024-01-01 10:05:00', '2024-01-01 10:15:00', '2024-01-01 10:20:00', # Thread 1 (a1)
            '2024-01-01 10:25:00', # Thread 1 reply to a3
            '2024-01-01 11:00:00', # Thread 2 (a5)
            '2024-02-15 12:10:00', '2024-02-15 12:20:00', # Thread 3 (b1, b2)
            '2024-02-15 12:30:00', # Thread 3 reply to non-existent b4
            '2024-01-01 11:30:00'  # Orphaned comment in Post A1

        ],
        'comment_text': ['...']*9,
        'comment_type': ['initial', 'reply', 'reply', 'reply', 'initial', 'initial', 'reply', 'reply', 'reply'],
        'reaction_count': [10, 5, 3, 1, 15, 2, 4, 6, 0]
    }
    df = pd.DataFrame(data)
    df['post_date'] = pd.to_datetime(df['post_date'])
    df['comment_date'] = pd.to_datetime(df['comment_date'])
    # Mimic potential empty string from CSV read
    df['parent_id'] = df['parent_id'].replace({np.nan: ''})
    return df

def test_calculate_features(sample_comments_df):
    """Tests the main functionality of calculate_graph_features.
    Checks that the output contains only id + 4 feature columns.
    """
    df_input = sample_comments_df.copy()
    df_result = calculate_graph_features(df_input)

    # --- Assertions --- 
    expected_cols = ['id', 'root_id', 'depth', 'sibling_count', 'time_since_root']
    assert sorted(df_result.columns.tolist()) == sorted(expected_cols), "Output columns mismatch"
    
    # Check data types of feature columns
    assert pd.api.types.is_object_dtype(df_result['root_id']) # or specific string dtype
    assert pd.api.types.is_integer_dtype(df_result['depth'])
    assert pd.api.types.is_integer_dtype(df_result['sibling_count'])
    assert pd.api.types.is_timedelta64_ns_dtype(df_result['time_since_root'])

    # Create expected values (adjust based on fixture data)
    expected_features = {
        # Post A1 (a1, a2, a3, a4) + (a5) + (a6-orphan)
        'a1': {'root_id': 'a1', 'depth': 0, 'sibling_count': 2, 'time_since_root': timedelta(0)}, # 3 roots (a1,a5,a6) -> count=2
        'a2': {'root_id': 'a1', 'depth': 1, 'sibling_count': 1, 'time_since_root': timedelta(minutes=10)},
        'a3': {'root_id': 'a1', 'depth': 1, 'sibling_count': 1, 'time_since_root': timedelta(minutes=15)},
        'a4': {'root_id': 'a1', 'depth': 2, 'sibling_count': 0, 'time_since_root': timedelta(minutes=20)},
        'a5': {'root_id': 'a5', 'depth': 0, 'sibling_count': 2, 'time_since_root': timedelta(0)}, # 3 roots (a1,a5,a6) -> count=2
        'a6': {'root_id': 'a6', 'depth': 0, 'sibling_count': 2, 'time_since_root': timedelta(0)}, # Orphaned; 3 roots (a1,a5,a6) -> count=2

        # Post B1 (b1, b2, b3)
        'b1': {'root_id': 'b1', 'depth': 0, 'sibling_count': 1, 'time_since_root': timedelta(0)}, # 2 roots (b1,b3) -> count=1
        'b2': {'root_id': 'b1', 'depth': 1, 'sibling_count': 0, 'time_since_root': timedelta(minutes=10)},
        'b3': {'root_id': 'b3', 'depth': 0, 'sibling_count': 1, 'time_since_root': timedelta(0)}, # Orphaned; 2 roots (b1,b3) -> count=1
    }

    # Check features for each comment ID
    result_features = df_result.set_index('id').to_dict(orient='index')
    assert len(result_features) == len(expected_features), "Mismatch in number of comments processed"
    
    for comment_id, expected in expected_features.items():
        assert comment_id in result_features, f"Comment ID {comment_id} missing in results"
        result = result_features[comment_id]
        assert result['root_id'] == expected['root_id'], f"Mismatch root_id for {comment_id}"
        assert result['depth'] == expected['depth'], f"Mismatch depth for {comment_id}"
        assert result['sibling_count'] == expected['sibling_count'], f"Mismatch sibling_count for {comment_id}"
        # Handle potential NaT comparison
        if pd.isna(expected['time_since_root']):
            assert pd.isna(result['time_since_root']), f"Mismatch time_since_root for {comment_id} (expected NaT)"
        else:
            assert result['time_since_root'] == expected['time_since_root'], f"Mismatch time_since_root for {comment_id}"

    # Check overall shape
    assert df_result.shape[0] == df_input.shape[0]


def test_empty_input():
    """Tests behavior with an empty DataFrame."""
    empty_df = pd.DataFrame(columns=['company_name', 'post_date', 'id', 'parent_id', 'comment_date', 'comment_text', 'comment_type', 'reaction_count'])
    # Ensure correct types for empty df processing
    empty_df['comment_date'] = pd.to_datetime(empty_df['comment_date'])
    empty_df['post_date'] = pd.to_datetime(empty_df['post_date'])
    
    df_result = calculate_graph_features(empty_df)
    
    # Expect an empty DataFrame with the specific feature columns
    expected_cols = ['id', 'root_id', 'depth', 'sibling_count', 'time_since_root']
    assert df_result.empty
    assert sorted(df_result.columns.tolist()) == sorted(expected_cols)
    

def test_input_without_grouping_cols():
    """Tests ValueError if grouping columns (company_name, post_date) are missing."""
    data = {
        'id': ['x1', 'x2'],
        'parent_id': ['', 'x1'],
        'comment_date': [pd.Timestamp('2024-01-01 10:00:00'), pd.Timestamp('2024-01-01 10:05:00')]
    }
    df_no_group = pd.DataFrame(data)
    # Update expected error message to match the earlier check for missing required columns
    with pytest.raises(ValueError, match="Input data is missing required column"):
        calculate_graph_features(df_no_group)

def test_input_with_nat_dates(sample_comments_df):
    """Tests handling of NaT in comment_date."""
    df_input = sample_comments_df.copy()
    # Introduce NaT for a root comment and a child comment
    df_input.loc[df_input['id'] == 'a1', 'comment_date'] = pd.NaT # Root
    df_input.loc[df_input['id'] == 'a2', 'comment_date'] = pd.NaT # Child
    
    df_result = calculate_graph_features(df_input)
    
    # Check the time_since_root for the comments with NaT dates
    assert pd.isna(df_result.loc[df_result['id'] == 'a1', 'time_since_root'].iloc[0])
    assert pd.isna(df_result.loc[df_result['id'] == 'a2', 'time_since_root'].iloc[0])
    # Check a sibling (a3) whose root (a1) is now NaT
    assert pd.isna(df_result.loc[df_result['id'] == 'a3', 'time_since_root'].iloc[0])
    # Check a child (a4) of a non-NaT parent (a3) but with a NaT root (a1)
    assert pd.isna(df_result.loc[df_result['id'] == 'a4', 'time_since_root'].iloc[0])
    # Check an unrelated comment's time is still calculated correctly
    assert df_result.loc[df_result['id'] == 'b2', 'time_since_root'].iloc[0] == timedelta(minutes=10)


# Consider adding more tests:
# - Test with only root comments
# - Test with very deep nesting
# - Test with non-string IDs if applicable
# - Test specific edge cases in sibling calculation if complex scenarios arise
