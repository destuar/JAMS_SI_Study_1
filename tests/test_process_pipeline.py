import pytest
import pandas as pd
import tempfile
import os
import shutil
from pathlib import Path

# Import the functions/classes to be tested
from scripts.preprocess.clean_comments import _clean_text, build_full_text, is_readable_comment
# We'll test clean_comments by running its main function
from scripts.preprocess.clean_comments import main as clean_comments_main

# --- Tests for _clean_text --- (Remains the same)

@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("Hello World", "hello world"),
        ("Check out https://example.com", "check out <url>"),
        ("Thanks @user1!", "thanks <mention>!"),
        ("This is great 👍", "this is great :thumbs_up:"),
        ("Mixed Case URL http://Test.Com/Path", "mixed case url <url>"),
        ("  Leading/Trailing Spaces  ", "leading/trailing spaces"),
        ("Multiple   spaces -> one", "multiple spaces -> one"),
        ("Emoji ❤️ and text", "emoji :red_heart: and text"),
        # Add more edge cases if needed
    ]
)
def test_clean_text(input_text, expected_output):
    """Tests the _clean_text function with various inputs."""
    assert _clean_text(input_text) == expected_output

# --- Tests for is_readable_comment short text filtering ---
@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("ok", False),           # 2 letters
        ("OK", False),           # uppercase
        ("No", False),           # 2 letters mixed case
        ("A", False),            # single letter
        ("5", False),            # single digit
        (":)", False),          # symbol length 2
        ("Hi!", True),           # 3 chars (len > 2), should pass
        ("Yes", True),           # 3 letters
        ("two", True),           # 3 letters lower
        ("hey there", True),     # >2 letters
    ]
)
def test_short_text_filter(input_text, expected):
    """Tests that comments of 2 characters or less (after cleaning) are filtered correctly."""
    # Apply cleaning logic (only lowercasing and whitespace for simplicity in test)
    cleaned = _clean_text(input_text)
    # Ensure we test the cleaned text
    assert is_readable_comment(cleaned) == expected

# --- Tests for clean_comments.py filtering --- 

@pytest.fixture
def sample_graphed_csv_with_unreadable(tmp_path) -> tuple[str, list[str]]:
    """Creates a sample graphed_comments.csv with readable and unreadable comments.
    
    Returns:
        tuple[str, list[str]]: Path to the CSV file and list of IDs expected to remain.
    """
    data = {
        'company_name': ['A'] * 8 + ['B'] * 7, # 15 total comments
        'post_date': ['2024-01-01 10:00:00'] * 15,
        'id': [f'c{i}' for i in range(1, 16)],
        'parent_id': ['', 'c1', 'c2', '', 'c4', '', 'c6', 'c7', 'c6', 'c9', '', '', '', '', 'c14'], 
        'comment_date': ['2024-01-01 10:05:00'] * 15,
        'comment_text': [
            # Readable
            "Root Comment 1 URL https://a.com", # c1 - Readable
            "Reply to c1 @mention",             # c2 - Readable
            "Reply to c2 👍",                   # c3 - Readable (emoji only but kept by logic)
            "Root Comment 4 UPPERCASE",          # c4 - Readable
            "Reply to c4   spaces",            # c5 - Readable
            "Root B1",                           # c6 - Readable
            "Reply B1-1",                        # c7 - Readable
            "Reply B1-1-1",                      # c8 - Readable
            "Reply B1-2",                        # c9 - Readable
            "Reply B1-2-1",                      # c10 - Readable
            # Unreadable
            "https://just.a.url.com",          # c11 - Filter: URL Only
            "",                                  # c12 - Filter: Empty
            None,                               # c13 - Filter: NaN/None
            "❤️❤️❤️",                             # c14 - Filter: Symbols/Emoji only (after demojize) 
            "Esto es español",                 # c15 - Filter: Non-English
        ],
        # --- Other columns needed by the script ---
        'comment_type': ['initial', 'reply'] * 7 + ['initial'],
        'reaction_count': list(range(1, 16)),
        'root_id': ['c1', 'c1', 'c1', 'c4', 'c4', 'c6', 'c6', 'c6', 'c6', 'c6', 'c11', 'c12', 'c13', 'c14', 'c14'],
        'depth': [0, 1, 2, 0, 1, 0, 1, 2, 1, 2, 0, 0, 0, 0, 1],
        'sibling_count': [0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0],
        'time_since_root': [pd.Timedelta(seconds=i) for i in range(15)],
        'before_DEI': ([1, 1, 0, 0, 1] * 3)[:15]
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "sample_graphed_unreadable.csv"
    df.to_csv(filepath, index=False)
    
    # Define which IDs should remain after filtering
    # c1-c10 are readable, c11-14 are filtered. c15 (Spanish) is now kept.
    expected_remaining_ids = [f'c{i}' for i in range(1, 11)] + ['c15'] # 11 IDs total
    # Note: c3 is kept because `is_readable` keeps emoji-only if short
    
    return str(filepath), expected_remaining_ids


def test_clean_thread_and_filter_comments(sample_graphed_csv_with_unreadable):
    """Tests clean_comments.py including the filtering of unreadable comments."""
    
    input_csv_path_str, expected_ids = sample_graphed_csv_with_unreadable
    input_csv_path = Path(input_csv_path_str)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        expected_output_csv = output_dir / "cleaned_threaded_comments.csv"
        
        # Run the main function
        clean_comments_main(str(input_csv_path), str(output_dir))

        # --- Assertions ---
        # 1. Check if output CSV is created
        assert expected_output_csv.exists(), "Output CSV file was not created."

        # 2. Load output CSV
        df_out = pd.read_csv(expected_output_csv)

        # 3. Check number of rows matches expected (now 11)
        assert len(df_out) == len(expected_ids), \
            f"Expected {len(expected_ids)} rows after filtering, but got {len(df_out)}"

        # 4. Check that only expected IDs remain
        output_ids = set(df_out['id'].tolist())
        assert output_ids == set(expected_ids), \
            f"Output IDs mismatch. Expected {set(expected_ids)}, Got {output_ids}"

        # Optional: Verify helper column is dropped (can be kept if useful)
        assert 'is_readable' not in df_out.columns 

# --- Test for build_full_text --- 
def test_build_full_text_logic():
    """Tests the build_full_text function directly with a simple hierarchy."""
    data = {
        'id': ['r1', 'r1_c1', 'r1_c1_c1', 'r2', 'r2_c1'],
        'parent_id': ['', 'r1', 'r1_c1', '', 'r2'],
        'cleaned_text': [
            "root one", 
            "reply one", 
            "reply one one", 
            "root two", 
            "reply two"
        ]
    }
    df = pd.DataFrame(data)
    
    # Build the required maps
    parent_map = df.set_index('id')['parent_id'].to_dict()
    text_map = df.set_index('id')['cleaned_text'].to_dict()

    # Apply the function using the maps
    df["full_text_test"] = df.apply(lambda row: build_full_text(row, parent_map, text_map), axis=1)
    
    # Expected outputs
    expected = {
        'r1': "root one",
        'r1_c1': "root one → reply one",
        'r1_c1_c1': "root one → reply one → reply one one", # 2 levels of ancestors
        'r2': "root two",
        'r2_c1': "root two → reply two"
    }

    # Verify
    for idx, row in df.iterrows():
        assert row["full_text_test"] == expected[row['id']], \
            f"Mismatch for id {row['id']}. Expected: {expected[row['id']]}, Got: {row['full_text_test']}"
