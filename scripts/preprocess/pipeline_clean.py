import re, emoji, spacy
from cleantext import clean
from spacy.language import Language

def _clean_text(txt: str) -> str:
    txt = txt.lower()
    txt = re.sub(r"https?://\\S+", "<url>", txt)
    txt = re.sub(r"@[\\w_]+", "<mention>", txt)
    txt = emoji.demojize(txt, delimiters=(" :", ": "))
    txt = clean(txt, no_line_breaks=True, no_punct=False)
    return txt.strip()

@Language.component("comment_cleaner")
def comment_cleaner(doc):
    cleaned = _clean_text(doc.text)
    return doc.from_docs([doc.vocab.make_doc(cleaned)])

# ── add to config.cfg -----------------------------------------
# [components]
# comment_cleaner = { }
# [nlp]
# pipeline = ["comment_cleaner","tok2vec","tagger", ...]
