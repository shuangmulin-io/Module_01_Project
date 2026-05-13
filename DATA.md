# Data Instructions

The source CSV is not included in this GitHub repository because it is too large for normal GitHub uploads.

To run the notebook or Streamlit app locally, place the dataset at:

```text
SGJobData.csv/SGJobData.csv
```

Expected local structure:

```text
Singapore_Job_Analytics/
|-- SGJobData.csv/
|   |-- SGJobData.csv
|-- Singapore_Jobs_Career_Switcher_Analytics.ipynb
|-- README.md
|-- requirements.txt
|-- DATA.md
```

The `SGJobData.csv/` folder is ignored by Git so the data can remain on your computer without being pushed to GitHub.

The Streamlit app uses this smaller processed file for deployment:

```text
data/singapore_jobs_processed.csv.gz
```

This deployment file keeps the most recent valid postings from the raw CSV to reduce memory usage on Streamlit Community Cloud.

To rebuild it from the raw CSV:

```bash
python scripts/build_processed_data.py
```

The Streamlit app also supports a remote CSV for deployment. In Streamlit Community Cloud, add a secret named `CSV_URL` that points to a direct downloadable CSV file.
