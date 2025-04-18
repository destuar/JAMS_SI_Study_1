import pandas as pd, spacy, pathlib, typer
import re, emoji # Add re and emoji imports
from spacy.tokens import DocBin, Doc

# Use blank nlp mainly for vocab and make_doc
nlp = spacy.blank("en") 
# REMOVED: nlp.add_pipe("comment_cleaner") 

# Register custom Doc extensions
Doc.set_extension("id", default=None)
Doc.set_extension("company", default=None)
Doc.set_extension("before_DEI", default=None)

# --- Text Cleaning Logic (inlined from pipeline_clean.py) ---
def _clean_text(txt: str) -> str:
    """Applies cleaning steps to comment text."""
    # Ensure input is a string
    if not isinstance(txt, str):
        txt = str(txt) # Attempt to convert non-strings
        
    txt = txt.lower()
    txt = re.sub(r"https?://\S+", "<url>", txt) 
    txt = re.sub(r"@\w+", "<mention>", txt)
    txt = emoji.demojize(txt, delimiters=(" :", ": "))
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()
# --- End Text Cleaning Logic ---

def main(src: str, out_dir: str):
    df = pd.read_csv(src)
    db_train = DocBin(store_user_data=True)
    db_dev   = DocBin(store_user_data=True)
    db_test  = DocBin(store_user_data=True)
    # stratify by brand to avoid leakage
    from sklearn.model_selection import StratifiedShuffleSplit
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    y = df["company_name"]
    train_idx, temp_idx = next(splitter.split(df, y))
    df_train = df.iloc[train_idx]; df_temp = df.iloc[temp_idx]
    # split temp 50‑50 into dev+test
    dev_idx, test_idx = next(
        StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
        .split(df_temp, df_temp["company_name"])
    )
    mapping = [("train", df_train, db_train),
               ("dev",   df_temp.iloc[dev_idx],  db_dev),
               ("test",  df_temp.iloc[test_idx], db_test)]
    for split, frame, db in mapping:
        for row in frame.itertuples():
            # 1. Clean text explicitly
            cleaned_text = _clean_text(row.comment_text or "")
            # 2. Create Doc from cleaned text
            doc = nlp.make_doc(cleaned_text)
            # 3. Assign attributes to this doc
            doc._.id           = row.id
            doc._.company      = row.company_name
            doc._.before_DEI   = row.before_DEI
            # 4. Add the final doc to DocBin
            db.add(doc)
        db.to_disk(pathlib.Path(out_dir)/f"{split}.spacy")
if __name__ == "__main__":
    typer.run(main)
