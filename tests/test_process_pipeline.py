import pytest
import pandas as pd
import spacy
from spacy.tokens import DocBin
import tempfile
import os
import shutil
from pathlib import Path

# Import the functions/classes to be tested
from scripts.preprocess.clean_comments import _clean_text
# We'll test clean_comments by running its main function
from scripts.preprocess.clean_comments import main as clean_comments_main

# --- Tests for _clean_text --- (now from clean_comments.py)

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

# --- Tests for clean_comments.py --- 

@pytest.fixture
def sample_graphed_csv(tmp_path) -> str:
    """Creates a sample graphed_comments.csv in a temporary directory."""
    data = {
        'company_name': ['A'] * 10 + ['B'] * 10, # Increased samples to 20 (10 A, 10 B)
        'post_date': ['2024-01-01 10:00:00'] * 20,
        'id': [f'c{i}' for i in range(1, 21)],
        'parent_id': ['', 'c1', '', 'c3', 'c1', '', 'c6', 'c6', '', 'c9'] * 2, # Repeat pattern
        'comment_date': ['2024-01-01 10:05:00'] * 20,
        'comment_text': [
            "Raw comment 1 URL https://a.com",
            "Comment 2 @mention",
            "Comment 3 👍",
            "Comment 4 UPPERCASE",
            "Comment 5   spaces",
            "Comment 6",
            "Comment 7",
            "Comment 8",
            "Comment 9",
            "Comment 10",
        ] * 2, # Repeat pattern
        'comment_type': ['initial', 'reply'] * 10,
        'reaction_count': list(range(1, 21)),
        'root_id': ['c1', 'c1', 'c3', 'c3', 'c1', 'c6', 'c6', 'c6', 'c9', 'c9'] * 2, # Repeat pattern
        'depth': [0, 1, 0, 1, 1, 0, 1, 1, 0, 1] * 2, # Repeat pattern
        'sibling_count': [1, 1, 0, 0, 1, 2, 2, 2, 0, 0] * 2, # Repeat pattern
        'time_since_root': [pd.Timedelta(0)] * 20,
        'before_DEI': ([1, 1, 0, 0, 1] + [1, 1, 1, 0, 0]) * 2 # Repeat pattern
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "sample_graphed.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


def test_convert_comments(sample_graphed_csv):
    """Tests the clean_comments.py script end-to-end."""
    
    # Use a temporary directory for DocBin outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        input_csv = sample_graphed_csv
        
        # Run the main function from clean_comments.py
        clean_comments_main(input_csv, str(output_dir))

        # --- Assertions ---
        # 1. Check if output files are created
        assert (output_dir / "train.spacy").exists()
        assert (output_dir / "dev.spacy").exists()
        assert (output_dir / "test.spacy").exists()

        # 2. Load one of the DocBins (e.g., test) and check contents
        nlp = spacy.blank("en") # Need a vocab to load DocBin
        doc_bin = DocBin().from_disk(output_dir / "test.spacy")
        docs = list(doc_bin.get_docs(nlp.vocab))

        # Check number of docs based on split ratio (20 items -> 14 train, 3 dev, 3 test)
        # 20 * 0.3 = 6 temp -> 6 * 0.5 = 3 dev, 3 test
        # Note: Stratified split might yield slightly different counts if rounding occurs
        assert len(docs) >= 2 and len(docs) <= 4, f"Expected 2-4 docs in test split, found {len(docs)}" 

        # 3. Check content of a sample doc
        if docs:
            sample_doc = docs[0]
            # Check if text was cleaned (example assumes c4 might land in test)
            # Find original text corresponding to the doc's ID
            doc_id = sample_doc._.id
            df_input = pd.read_csv(input_csv)
            
            # --- Debugging Prints ---
            # print(f"\nDEBUG: doc_id from sample_doc._.id = {repr(doc_id)}")
            # print(f"DEBUG: Unique IDs in df_input = {df_input['id'].unique()}")
            # id_match_series = df_input['id'] == doc_id
            # print(f"DEBUG: Result of (df_input['id'] == doc_id).any() = {id_match_series.any()}")
            # --- End Debugging Prints ---
            
            # Find the row matching the doc_id
            id_match_series = df_input['id'] == doc_id
            if not id_match_series.any():
                raise ValueError(f"Test Error: doc_id '{doc_id}' not found in input CSV.")
            original_text = df_input.loc[id_match_series, 'comment_text'].iloc[0]
            
            expected_cleaned_text = _clean_text(original_text)
            
            assert sample_doc.text == expected_cleaned_text, "Doc text doesn't match expected cleaned text"
            
            # Check custom attributes
            assert hasattr(sample_doc._, 'id')
            assert hasattr(sample_doc._, 'company')
            assert hasattr(sample_doc._, 'before_DEI')
            assert sample_doc._.id is not None
            assert sample_doc._.company in ['A', 'B']
            assert sample_doc._.before_DEI in [0, 1]
