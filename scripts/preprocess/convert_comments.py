import pandas as pd, spacy, pathlib, typer
from spacy.tokens import DocBin, Doc
nlp = spacy.blank("en")
nlp.add_pipe("comment_cleaner")

def main(src: str, out_dir: str):
    df = pd.read_csv(src)
    db_train = DocBin()
    db_dev   = DocBin()
    db_test  = DocBin()
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
            doc = nlp(row.comment_text or "")
            doc._.id           = row.id
            doc._.company      = row.company_name
            doc._.before_DEI   = row.before_DEI
            db.add(doc)
        db.to_disk(pathlib.Path(out_dir)/f"{split}.spacy")
if __name__ == "__main__":
    typer.run(main)
