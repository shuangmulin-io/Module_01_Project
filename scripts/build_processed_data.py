import ast
import re
from pathlib import Path

import pandas as pd


RAW_CSV_PATH = Path("SGJobData.csv") / "SGJobData.csv"
OUTPUT_PATH = Path("data") / "singapore_jobs_processed.csv.gz"

SKILL_KEYWORDS = [
    "python",
    "sql",
    "excel",
    "power bi",
    "tableau",
    "java",
    "javascript",
    "react",
    "aws",
    "azure",
    "cloud",
    "data",
    "analytics",
    "machine learning",
    "ai",
    "cybersecurity",
    "devops",
    "sales",
    "marketing",
    "finance",
    "accounting",
    "project management",
]


def extract_primary_category(value: object) -> str:
    if pd.isna(value):
        return "Unspecified"

    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return "Unspecified"

    if not parsed:
        return "Unspecified"

    first_category = parsed[0]
    if isinstance(first_category, dict):
        return first_category.get("category", "Unspecified")

    return "Unspecified"


def classify_role_family(title: object) -> str:
    text = str(title).lower()
    role_patterns = {
        "Data & Analytics": r"\b(data|analyst|analytics|business intelligence|bi)\b",
        "Software & Engineering": r"\b(software|developer|engineer|programmer|java|python|frontend|backend|full stack)\b",
        "Cybersecurity & Infrastructure": r"\b(cyber|security|network|infrastructure|systems|cloud|devops)\b",
        "Finance & Accounting": r"\b(finance|account|audit|tax|payroll|treasury)\b",
        "Sales & Marketing": r"\b(sales|marketing|brand|growth|business development|digital marketing)\b",
        "Operations & Supply Chain": r"\b(operation|supply|logistics|warehouse|procurement|planner)\b",
        "HR & Administration": r"\b(hr|human resource|recruit|admin|secretary|office)\b",
        "Healthcare & Life Sciences": r"\b(nurse|medical|health|clinic|pharma|laboratory|technologist)\b",
    }

    for family, pattern in role_patterns.items():
        if re.search(pattern, text):
            return family

    return "Other Roles"


def extract_skill_signals(title: object) -> str:
    text = str(title).lower()
    matched_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"
        if re.search(pattern, text):
            matched_skills.append(skill.title())

    return ", ".join(matched_skills)


def classify_seniority(row: pd.Series) -> str:
    position_level = str(row.get("positionLevels", "")).lower()
    title = str(row.get("title", "")).lower()
    years = row.get("minimumYearsExperience", 0)

    if pd.isna(years):
        years = 0

    if any(term in title for term in ["intern", "trainee", "fresh graduate", "entry level"]):
        return "Entry Level"
    if "manager" in position_level or any(term in title for term in ["manager", "lead", "principal", "head"]):
        return "Manager & Lead"
    if "senior" in position_level or "senior" in title or years >= 5:
        return "Senior"
    if years <= 1:
        return "Entry Level"
    if years <= 4:
        return "Mid Level"

    return "Unspecified"


def main() -> None:
    if not RAW_CSV_PATH.exists():
        raise FileNotFoundError(f"Raw CSV not found at {RAW_CSV_PATH}")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    usecols = [
        "categories",
        "employmentTypes",
        "metadata_jobPostId",
        "metadata_newPostingDate",
        "metadata_totalNumberJobApplication",
        "metadata_totalNumberOfView",
        "minimumYearsExperience",
        "numberOfVacancies",
        "positionLevels",
        "postedCompany_name",
        "salary_maximum",
        "salary_minimum",
        "salary_type",
        "status_jobStatus",
        "title",
        "average_salary",
    ]
    output_columns = [
        "metadata_jobPostId",
        "title",
        "postedCompany_name",
        "category",
        "role_family",
        "seniority",
        "employmentTypes",
        "minimumYearsExperience",
        "salary_minimum",
        "salary_maximum",
        "average_salary",
        "salary_type",
        "numberOfVacancies",
        "metadata_newPostingDate",
        "metadata_totalNumberJobApplication",
        "metadata_totalNumberOfView",
        "status_jobStatus",
        "skill_signals",
    ]

    first_chunk = True
    total_rows = 0
    for chunk in pd.read_csv(RAW_CSV_PATH, usecols=usecols, chunksize=50_000):
        chunk["metadata_newPostingDate"] = pd.to_datetime(chunk["metadata_newPostingDate"], errors="coerce")

        salary_mask = (
            chunk["salary_type"].eq("Monthly")
            & chunk["metadata_newPostingDate"].notna()
            & chunk["average_salary"].notna()
            & chunk["average_salary"].between(500, 50_000)
            & chunk["salary_minimum"].between(0, 50_000)
            & chunk["salary_maximum"].between(0, 70_000)
        )
        chunk = chunk.loc[salary_mask].copy()

        chunk["category"] = chunk["categories"].apply(extract_primary_category)
        chunk["role_family"] = chunk["title"].apply(classify_role_family)
        chunk["skill_signals"] = chunk["title"].apply(extract_skill_signals)
        chunk["seniority"] = chunk.apply(classify_seniority, axis=1)

        processed = chunk[output_columns].drop_duplicates()
        processed.to_csv(
            OUTPUT_PATH,
            mode="wt" if first_chunk else "at",
            index=False,
            header=first_chunk,
            compression="gzip",
        )
        total_rows += len(processed)
        first_chunk = False

    file_size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Wrote {total_rows:,} rows to {OUTPUT_PATH} ({file_size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
