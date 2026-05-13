# Singapore Job Analytics

This project analyses Singapore job-posting data for **jobseekers and career switchers**.

The main question is:

> Which skills should I learn to improve employability?

The notebook builds a career-guidance analytics prototype that highlights in-demand skills, salary trends, entry-level vs senior-level opportunities, and role pathways.

## Project Files

- `app.py` - Streamlit dashboard that loads the CSV with Pandas for interactive filtering, charts, and job exploration.
- `data/singapore_jobs_processed.csv.gz` - compressed deployment dataset used by the Streamlit app.
- `scripts/build_processed_data.py` - rebuilds the compressed deployment dataset from the raw local CSV.
- `Singapore_Jobs_Career_Switcher_Analytics.ipynb` - main Jupyter notebook with data cleaning, feature engineering, analysis, charts, dashboard-style filters, and report draft.
- `Singapore_Jobs_DuckDB_SQL_Analytics.ipynb` - alternative notebook that loads the CSV into DuckDB first, performs cleaning and analysis with SQL, then uses matplotlib for dashboard charts.
- `requirements.txt` - Python packages needed to run the Streamlit app and notebooks.
- `DATA.md` - instructions for placing the large CSV locally.
- `.gitignore` - excludes large local data files, notebook checkpoints, virtual environments, and cache files.

## Data

The dataset is not committed to this repository because the CSV is too large for a normal GitHub push.

Place the CSV locally at:

```text
SGJobData.csv/SGJobData.csv
```

See `DATA.md` for the expected folder structure.

The Streamlit app uses a smaller compressed file at:

```text
data/singapore_jobs_processed.csv.gz
```

This file is created from the raw CSV and keeps the most recent valid postings so it stays small enough for GitHub and Streamlit Community Cloud. To rebuild it after updating the raw CSV:

```bash
python scripts/build_processed_data.py
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

Start Jupyter:

```bash
jupyter notebook
```

Then open either notebook:

```text
Singapore_Jobs_Career_Switcher_Analytics.ipynb
Singapore_Jobs_DuckDB_SQL_Analytics.ipynb
```

## Analysis Focus

The notebook supports the assignment brief through:

- Business case for jobseekers and career switchers
- Data loading and cleaning process
- Salary filtering and salary-band creation
- Seniority classification using position level, title, and minimum experience
- Role-family classification from job titles
- Skill extraction from visible title keywords
- Demand, salary, competition, and employability scoring
- Dashboard-style views for skills, salaries, entry-level access, and role pathways

## Important Limitation

The CSV does not include full job descriptions, so skill extraction is based mainly on job titles. Skill counts should be interpreted as visible skill signals rather than a complete view of every requirement in each job posting.

## Streamlit Deployment

The app uses Pandas and does not require DuckDB. For local use, place the dataset at `SGJobData.csv/SGJobData.csv`.

For Streamlit Community Cloud, push `data/singapore_jobs_processed.csv.gz` with the app. You can also provide a direct CSV URL through Streamlit secrets as `CSV_URL` if you later move the data to external storage. The large raw data folder and database files are ignored by Git and should not be pushed to GitHub.
