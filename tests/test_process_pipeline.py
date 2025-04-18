import pytest
import pandas as pd
import spacy
from spacy.tokens import DocBin
import tempfile
import os
import shutil
from pathlib import Path

# Import the functions/classes to be tested
from scripts.preprocess.pipeline_clean import _clean_text
# We'll test convert_comments by running its main function
from scripts.preprocess.convert_comments import main as convert_comments_main

# --- Tests for _clean_text --- (from pipeline_clean.py)

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

# --- Tests for convert_comments.py --- 

@pytest.fixture
def sample_graphed_csv(tmp_path) -> str:
    """Creates a sample graphed_comments.csv in a temporary directory."""
    data = {
        'company_name': ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B', 'A', 'B'], # Ensure enough samples for split
        'post_date': ['2024-01-01 10:00:00'] * 10,
        'id': [f'c{i}' for i in range(1, 11)],
        'parent_id': ['', 'c1', '', 'c3', 'c1', '', 'c6', 'c6', '', 'c9'],
        'comment_date': ['2024-01-01 10:05:00'] * 10,
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
        ],
        'comment_type': ['initial', 'reply'] * 5,
        'reaction_count': [1,2,3,4,5,6,7,8,9,10],
        'root_id': ['c1', 'c1', 'c3', 'c3', 'c1', 'c6', 'c6', 'c6', 'c9', 'c9'],
        'depth': [0, 1, 0, 1, 1, 0, 1, 1, 0, 1],
        'sibling_count': [1, 1, 0, 0, 1, 2, 2, 2, 0, 0],
        'time_since_root': [pd.Timedelta(0)] * 10,
        'before_DEI': [1, 1, 0, 0, 1, 1, 1, 1, 0, 0] # Example flags
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "sample_graphed.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


def test_convert_comments(sample_graphed_csv):
    """Tests the convert_comments.py script end-to-end."""
    
    # Use a temporary directory for DocBin outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        input_csv = sample_graphed_csv
        
        # Run the main function from convert_comments.py
        convert_comments_main(input_csv, str(output_dir))

        # --- Assertions ---
        # 1. Check if output files are created
        assert (output_dir / "train.spacy").exists()
        assert (output_dir / "dev.spacy").exists()
        assert (output_dir / "test.spacy").exists()

        # 2. Load one of the DocBins (e.g., test) and check contents
        nlp = spacy.blank("en") # Need a vocab to load DocBin
        doc_bin = DocBin().from_disk(output_dir / "test.spacy")
        docs = list(doc_bin.get_docs(nlp.vocab))

        # Check number of docs based on split ratio (10 items -> 7 train, 1 dev, 2 test? Or 7/1/2? Check script logic -> 70/15/15)
        # 10 * 0.3 = 3 temp -> 3 * 0.5 = 1.5 -> 1 dev, 2 test (approx)
        # Note: Stratified split might yield slightly different counts
        assert len(docs) >= 1 and len(docs) <= 2, f"Expected 1 or 2 docs in test split, found {len(docs)}" 

        # 3. Check content of a sample doc
        if docs:
            sample_doc = docs[0]
            # Check if text was cleaned (example assumes c4 might land in test)
            # Find original text corresponding to the doc's ID
            doc_id = sample_doc._.id 
            df_input = pd.read_csv(input_csv)
            original_text = df_input.loc[df_input['id'] == doc_id, 'comment_text'].iloc[0]
            expected_cleaned_text = _clean_text(original_text)
            
            assert sample_doc.text == expected_cleaned_text, "Doc text doesn't match expected cleaned text"
            
            # Check custom attributes
            assert hasattr(sample_doc._, 'id')
            assert hasattr(sample_doc._, 'company')
            assert hasattr(sample_doc._, 'before_DEI')
            assert sample_doc._.id is not None
            assert sample_doc._.company in ['A', 'B']
            assert sample_doc._.before_DEI in [0, 1]
