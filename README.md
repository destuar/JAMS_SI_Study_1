# Facebook Public Comment Collector

## Project Goal

This project provides a methodology and tools for manually collecting publicly available comments from specific Facebook company posts. The primary goal is to gather comment text and approximate timestamps for research and analysis purposes, focusing solely on the content of the comments themselves, not personal user information.

**Compliance:** This process is designed to be manual and respects Meta's Terms of Service by **not** performing automated scraping of user data. Only publicly visible comment text and relative timestamps are targeted.

## Methodology

The process involves two main phases:

1.  **Manual Extraction:** Using a JavaScript snippet run in the browser's developer console on a specific Facebook post page to extract visible comments into a JSON format.
2.  **Processing:** Using a Python script to process a single JSON file (representing one post's comments) at a time, calculate approximate dates, add metadata (company name, post date), and save the relevant information into a structured CSV file.

## File Structure

The project expects the following directory structure:

```
/Your/Project/Root/ (e.g., Namin, Ketron, Mai/)
|-- comment_extractor.js       # JavaScript snippet for manual extraction
|-- process_comments_json.py   # Python script for processing JSON files
|-- README.md                  # This file
|
|-- CompanyName1/              # Folder for Company 1 (e.g., Target)
|   |-- MM_DD_YY_HHMM[AM|PM].json  # JSON output for a post from Company 1
|   |-- MM_DD_YY_HHMM[AM|PM].csv   # CSV output generated from the JSON file
|   |-- ... (more posts)
|
|-- CompanyName2/              # Folder for Company 2 (e.g., Microsoft)
|   |-- MM_DD_YY_HHMM[AM|PM].json
|   |-- MM_DD_YY_HHMM[AM|PM].csv
|   |-- ...
|
|-- ... (more companies)
```

## Usage Instructions

### Phase 1: Manual Comment Extraction (Per Post)

**Prerequisites:**
*   A modern web browser (like Chrome, Firefox, Edge) with access to Developer Tools.
*   Logged into Facebook.

**Steps (Repeat for each target Facebook post):**

1.  **Navigate & Scroll:** Open the specific Facebook post page in your browser.
2.  **Load All Comments:** Scroll down the comments section repeatedly. Click *all* relevant links like "View more comments", "View X replies", etc., until no more comments load and you have reached the beginning of the comment thread.
3.  **Open Developer Console:** Press `F12` (or right-click on the page and select "Inspect" or "Inspect Element", then navigate to the "Console" tab).
4.  **Copy Extractor Code:** Open the `comment_extractor.js` file in a text editor and copy its entire content.
5.  **Run Extractor Code:** Paste the copied JavaScript code into the browser's console where the cursor is blinking and press `Enter`.
6.  **Copy JSON Output:** The script will log the number of comments found and extracted. It will then output a block of text starting with `[` and ending with `]`. This is the JSON data, containing a list of comment objects. Each object includes:
    *   `id`: A unique identifier for the comment or reply.
    *   `parent_id`: The `id` of the comment this one is directly replying to (null for initial comments).
    *   `text`: The main text content of the comment.
    *   `timestamp_text`: The relative time text (e.g., "5w", "2d").
    *   `reaction_count`: The number of reactions on the comment.
    *   `comment_type`: Indicates if it's an `'initial'` comment or a `'reply'`.
    Carefully select and copy this entire JSON block.
7.  **Save JSON File:**
    *   Open a plain text editor (like Notepad, TextEdit, VS Code).
    *   Paste the copied JSON data.
    *   Determine the approximate date and time of the *original Facebook post*.
    *   Save the file with a specific name format: `MM_DD_YY_HHMM[AM|PM].json` (e.g., `02_03_25_0953AM.json` for Feb 03, 2025, 9:53 AM).
    *   Save this file inside the correct company-specific folder (e.g., `Target/`, `Microsoft/`).

### Phase 2: Processing JSON to CSV (Per File)

**Prerequisites:**
*   Python 3 installed.
*   Required Python libraries: `pandas` and `python-dateutil`.

**Installation (if needed):**
Open your terminal or command prompt and run:
```bash
pip install pandas python-dateutil
# or if you use pip3
pip3 install pandas python-dateutil
```

**Steps:**

1.  **Open Terminal:** Open your terminal or command prompt.
2.  **Navigate to Root Directory:** Use the `cd` command to navigate to the main project directory where `process_comments_json.py` and the company folders are located.
    ```bash
    cd "/path/to/your/project/root" 
    # Example: cd "/Users/diegoestuar/Desktop/CGU PhD/Research/Namin, Ketron, Mai"
    ```
3.  **Run Python Script:** Execute the script using Python 3.
    ```bash
    python3 process_comments_json.py
    ```
4.  **Enter Company Name:** The script will prompt: `Enter the company name (folder name, e.g., Target):`. Type the exact name of the folder containing the JSON file you want to process (e.g., `Target`) and press `Enter`.
5.  **Enter Filename (Date/Time):** The script will prompt: `Enter the date & time (file name without .json, e.g., 02_03_25_0953AM):`. Type the exact name of the file you want to process, *without* the `.json` extension (e.g., `02_03_25_0953AM`), and press `Enter`.
6.  **Processing:** The script will process the specified JSON file, calculate dates, add metadata, and save the results.
7.  **Check Output:** Navigate to the company folder (e.g., `Target/`). You will find a new CSV file named identically to the JSON file but with a `.csv` extension (e.g., `02_03_25_0953AM.csv`).

## Output CSV Format

The generated CSV file will contain the following columns:

*   `company_name`: The name of the company (derived from the folder name provided).
*   `post_date`: The approximate date and time of the original Facebook post (parsed from the filename, formatted as `YYYY-MM-DD HH:MM:SS`).
*   `comment_text`: The extracted text content of the comment.
*   `comment_date`: The approximate date the comment was made (calculated from the relative timestamp like "5w", "2d", formatted as `YYYY-MM-DD`). Empty if the date could not be parsed.
*   `id`: The unique identifier for the comment/reply from the JSON.
*   `parent_id`: The identifier of the direct parent comment/reply (empty for initial comments).
*   `reaction_count`: The number of reactions counted for the comment.
*   `comment_type`: Type of the comment ('initial' or 'reply').

## Ethics Statement and Data Collection Justification

Comment data from public Facebook posts was collected using a **manual and user-initiated process** that does not rely on automated scraping, bots, or circumvention of access controls. The collection method involved:

- A human researcher manually navigating to publicly visible Facebook posts on a logged-in account.
- Manually loading all comments through user interface interactions (e.g., clicking “View more comments,” “View more replies”).
- Running a JavaScript snippet in the browser’s developer console to extract only the visible comment text, relative timestamp text (e.g., "2d", "5w"), and reaction count.
- Saving the extracted comments in JSON format for processing and anonymization.

No personal identifying information (PII) such as usernames, user IDs, profile links, or photos was collected, stored, or analyzed. The data was restricted to comment text, approximate timing, comment/reply structure, and publicly visible engagement counts.

The methodology was designed to **respect Meta’s Terms of Service**, as it:
- Does not perform any automated scraping or crawling,
- Does not circumvent access controls, authentication, or privacy settings,
- Does not access private groups or content,
- Involves only human-initiated interactions through a standard user interface,
- Extracts only data already visible in the browser's rendered DOM.

This project adheres to the principles of ethical research, including the avoidance of harm, respect for individual privacy, and responsible data stewardship. Data was collected solely for academic research and analysis purposes. No commercial use is intended or permitted.

