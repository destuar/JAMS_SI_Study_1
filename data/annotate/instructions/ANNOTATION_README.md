# Facebook DEI Comment - Relevance Annotation Task

This document describes how to set up and perform the relevance annotation task using Label Studio.

The goal of this task is to label comments from `relevance_sample.csv` as either relevant or not relevant to Diversity, Equity, and Inclusion (DEI) topics.

## 1. Setup Label Studio

The recommended way to run Label Studio is using Docker for consistency.

1.  **Install Docker:** If you don't have Docker installed, follow the instructions for your OS: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
2.  **Run Label Studio Container:** Open your terminal, navigate to the root directory of this project (`Facebook-TextAnalytics-Project`), and run the following command:

    ```bash
    docker run -it -p 8080:8080 -v $(pwd)/data/annotate/ls_data:/label-studio/data heartexlabs/label-studio:latest
    ```

    *   This command starts Label Studio and makes it accessible at `http://localhost:8080` in your browser.
    *   It also mounts a local directory (`data/annotate/ls_data`) inside the container to persist Label Studio's data. You might need to create this directory (`mkdir -p data/annotate/ls_data`) if it doesn't exist.

3.  **Access Label Studio:** Open `http://localhost:8080` in your web browser. You may need to sign up for a free account the first time.

## 2. Create and Configure the Project

1.  **Create Project:**
    *   Click `Create Project`.
    *   Enter a project name (e.g., "DEI Comment Relevance").
    *   Optionally, add a description.
2.  **Import Data:**
    *   Go to the `Data Import` tab.
    *   Click `Upload Files`.
    *   Select the input file for this task: `data/annotate/relevance_sample.csv` (relative to the project root).
    *   Label Studio should automatically detect it as a CSV file.
    *   Click `Import`.
3.  **Setup Labeling Interface:**
    *   Go to `Settings` -> `Labeling Interface`.
    *   Click `Browse Templates` and select the `Custom template` option.
    *   Click on the `Code` tab.
    *   Delete the default content in the code editor.
    *   Open the file `data/annotate/instructions/relevance_labeling_config.xml` (relative to the project root) in a text editor.
    *   Copy the entire content of `relevance_labeling_config.xml`.
    *   Paste the copied XML content into the Label Studio `Code` editor.
    *   Click `Save`.

## 3. Perform Annotation

1.  **Start Labeling:** Go back to the project's main page and click `Start Labeling` or select tasks from the `Data Manager`.
2.  **Guidelines:** For each comment displayed (`full_text`):
    *   Read the comment text.
    *   Decide if the comment is **relevant** to the topic of Diversity, Equity, and Inclusion (DEI).
    *   Select **`1 (Relevant)`** if it discusses or relates to DEI initiatives, concepts, policies, hiring, representation, etc.
    *   Select **`0 (Not Relevant)`** if the comment is unrelated to DEI (e.g., general product feedback, spam, off-topic discussions).
    *   Click `Submit` to save the annotation and move to the next task.

## 4. Export Results

Once annotation is complete (or partially complete):

1.  **Go to Data Manager:** Navigate to the project's `Data Manager` view (usually the default view showing the table of tasks).
2.  **Click Export:** Find and click the `Export` button.
3.  **Select Format:** Choose the `JSON` format. This is the format the conversion script expects.
4.  **Download:** Click `Export` to download the results as a JSON file.
5.  **Save File:** Save the downloaded JSON file into the `data/annotate/` directory. You can keep the default name (like `project-1-at-YYYY-MM-DD-HH-MM-hash.json`) or rename it if desired (e.g., `annotated_relevance.json`).

## 5. Convert Exported JSON to CSV (Optional)

A Python script is provided to convert the exported JSON file into a more tabular CSV format, similar to the one used in the main workflow.

1.  **Ensure Script Exists:** Make sure you have the `json_to_csv.py` script located at `scripts/annotate/json_to_csv.py`.
2.  **Run Script:** Open your terminal in the project's root directory and run:

    ```bash
    python scripts/annotate/json_to_csv.py data/annotate/<your_exported_json_file.json> data/annotate/review/annotated_relevance.csv
    ```

    Replace `<your_exported_json_file.json>` with the **actual name of the file you downloaded** from Label Studio in Step 4. The target path (`data/annotate/review/annotated_relevance.csv`) acts as the base name; the script will add numbers if this file (or subsequent numbered versions) already exists in the `review` folder.

    Alternatively, you can navigate to the scripts directory and run it (adjusting paths):
    ```bash
    cd scripts/annotate
    python json_to_csv.py ../../data/annotate/<your_exported_json_file.json> ../../data/annotate/review/annotated_relevance.csv
    cd ../.. # Go back to project root
    ```

    Running the script with its default paths (as coded) requires the input JSON and desired output CSV to be relative to where you *run* the `python` command from.
    Example using default paths (run from project root):
    ```bash
    # This assumes the script's default input is 'data/annotate/project-1-at-....json'
    # (Make sure this default file actually exists if you use this command)
    # and the default base output is 'data/annotate/review/annotated_relevance.csv'
    python scripts/annotate/json_to_csv.py 
    ```

    This will create a CSV file (e.g., `data/annotate/review/annotated_relevance.csv`) containing the original data fields plus the annotation results (`relevance_choice`). 