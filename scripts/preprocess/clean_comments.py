import pandas as pd
from pathlib import Path
import typer
import re
import emoji
import string
import unicodedata

# --- Text Cleaning Logic ---
def _clean_text(txt: str) -> str:
    """Applies cleaning steps to comment text."""
    if not isinstance(txt, str):
        txt = str(txt)

    # 1. Unicode normalization
    try:
        txt = unicodedata.normalize('NFKC', txt)
    except TypeError:
        # Handle potential errors if input is not a valid string for normalization
        return "" # Or handle as appropriate, e.g., log error
        
    # 2. Lowercase
    txt = txt.lower()

    # 3. Replace URLs/Mentions
    txt = re.sub(r"https?://\S+", "<url>", txt)
    txt = re.sub(r"@\w+", "<mention>", txt)

    # 4. Demojize (handles emojis)
    txt = emoji.demojize(txt, delimiters=(" :", ": "))

    # 5. Character Filtering (Keep letters, numbers, standard punc, whitespace, colons, < >)
    # Define allowed characters explicitly
    allowed_chars = string.ascii_lowercase + string.digits + string.punctuation + string.whitespace + ":<>"
    # Remove characters not in the allowed set
    txt = ''.join(c for c in txt if c in allowed_chars)
    
    # 6. Normalize whitespace (after potential character removals)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

# --- Ancestor-based full_text Construction ---
def build_full_text(row, parent_map: dict, text_map: dict) -> str:
    """Prepend up to two cleaned-ancestor texts to the current comment."""
    cleaned = row["cleaned_text"]
    pid1 = row.get("parent_id")
    if pd.isna(pid1) or pid1 == "" or pid1 not in text_map:
        return cleaned
    parent_text = text_map[pid1]
    pid2 = parent_map.get(pid1)
    if pd.isna(pid2) or pid2 == "" or pid2 not in text_map:
        return f"{parent_text} → {cleaned}"
    grandparent_text = text_map[pid2]
    return f"{grandparent_text} → {parent_text} → {cleaned}"

# --- Readability Filtering Logic (SIMPLIFIED + Refined Symbol Check v3) ---
def is_readable_comment(text: str) -> bool:
    """Checks if a cleaned comment has basic validity and meaningful content beyond placeholders/emojis."""
    # 1. Basic validity checks
    if pd.isna(text): return False
    text = str(text).strip()
    if not text: return False
    low = text.lower()
    if low in ("none", "nan"): return False
    if len(low) <= 2: return False

    # 2. Check for placeholder-only comments
    cleaned_no_placeholders = re.sub(r"<url>|<mention>", "", text).strip()
    if not cleaned_no_placeholders:
        return False
    if low == "<url>" or low == "<mention>": 
        return False

    # 3. Check if content exists beyond placeholders AND demojized emojis
    # Start with text after removing placeholders
    temp_text = cleaned_no_placeholders
    # Remove demojized emoji patterns like :word:
    text_no_emojis = re.sub(r":([a-zA-Z0-9_]+):", "", temp_text).strip()

    # If nothing is left after removing placeholders and emoji patterns, filter
    if not text_no_emojis:
         # print(f"Filtering: Only placeholders/emojis found in '{text}'")
         return False

    # Optional: Check again for only punctuation/whitespace remaining *after* emoji removal
    # This catches cases like ":)" or "!!! " which might have been left
    # Use re.escape to handle punctuation safely in the character set
    if re.fullmatch(r"[" + re.escape(string.punctuation + string.whitespace) + r"]*", text_no_emojis):
         # print(f"Filtering: Only punctuation/whitespace left after emoji removal in '{text}' -> '{text_no_emojis}'")
          return False

    # 4. Language check REMOVED - too unreliable for this context.

    # Passed all filters
    return True

def main(src: str, out_dir: str):
    """Phase 3: Text Preprocessing, Thread Creation & Filtering"""
    # Load data
    df = pd.read_csv(src)

    # Step 3a: Clean the comment_text field
    df["cleaned_text"] = df["comment_text"].apply(_clean_text)

    # Build lookup maps
    parent_map = df.set_index("id")["parent_id"].to_dict() # Restored
    text_map = df.set_index("id")["cleaned_text"].to_dict() # Restored

    # Step 3b: Build full_text with ancestor context
    df["full_text"] = df.apply(lambda row: build_full_text(row, parent_map, text_map), axis=1) # Restored
    
    # Step 3c: Filter out non-readable comments using the REVISED function
    initial_rows = len(df)
    df["is_readable"] = df["cleaned_text"].apply(is_readable_comment) 
    df_filtered = df[df["is_readable"]].copy()
    filtered_rows = len(df_filtered)
    print(f"Filtered out {initial_rows - filtered_rows} non-readable comments.")
    
    # Drop the helper column before saving
    df_filtered.drop(columns=["is_readable"], inplace=True)

    # Write filtered cleaned threaded comments
    out_path = Path(out_dir) / "cleaned_threaded_comments.csv"
    df_filtered.to_csv(out_path, index=False)


if __name__ == "__main__":
    typer.run(main)
