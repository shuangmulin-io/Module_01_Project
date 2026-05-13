import ast
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Singapore Job Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)

LOCAL_CSV_PATH = Path("SGJobData.csv") / "SGJobData.csv"
PROCESSED_CSV_PATH = Path("data") / "singapore_jobs_processed.csv.gz"
DEFAULT_CSV_SOURCE = str(PROCESSED_CSV_PATH)

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

SENIORITY_ORDER = ["Entry Level", "Mid Level", "Senior", "Manager & Lead"]


@st.cache_data(show_spinner="Loading job data...")
def load_data(csv_source: str) -> pd.DataFrame:
    df = pd.read_csv(csv_source)

    date_columns = [
        "metadata_newPostingDate",
        "metadata_originalPostingDate",
        "metadata_expiryDate",
    ]
    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    numeric_columns = [
        "salary_minimum",
        "salary_maximum",
        "average_salary",
        "minimumYearsExperience",
        "metadata_totalNumberJobApplication",
        "metadata_totalNumberOfView",
        "numberOfVacancies",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "category" not in df.columns and "categories" in df.columns:
        df["category"] = df["categories"].apply(extract_primary_category)
    if "role_family" not in df.columns:
        df["role_family"] = df["title"].apply(classify_role_family)
    if "skill_signals" not in df.columns:
        df["skill_signals"] = df["title"].apply(extract_skill_signals)
    else:
        df["skill_signals"] = df["skill_signals"].fillna("").apply(split_skill_signals)
    if "seniority" not in df.columns:
        df["seniority"] = df.apply(classify_seniority, axis=1)

    return df


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


def extract_skill_signals(title: object) -> list[str]:
    text = str(title).lower()
    matched_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"
        if re.search(pattern, text):
            matched_skills.append(skill.title())

    return matched_skills


def split_skill_signals(value: object) -> list[str]:
    if pd.isna(value) or str(value).strip() == "":
        return []

    return [skill.strip() for skill in str(value).split(",") if skill.strip()]


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


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"S${value:,.0f}"


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")

        search_text = st.text_input("Search job title or company")

        categories = sorted(df["category"].dropna().unique())
        selected_categories = st.multiselect("Industry / Job Category", categories)

        role_families = sorted(df["role_family"].dropna().unique())
        selected_role_families = st.multiselect("Career Track", role_families)

        available_seniorities = df["seniority"].dropna().unique().tolist()
        seniorities = [level for level in SENIORITY_ORDER if level in available_seniorities]
        seniorities += sorted(level for level in available_seniorities if level not in SENIORITY_ORDER)
        selected_seniorities = st.multiselect("Seniority", seniorities)

        employment_types = sorted(df["employmentTypes"].dropna().unique())
        selected_employment_types = st.multiselect("Employment type", employment_types)

        min_salary = int(df["average_salary"].dropna().min())
        max_salary = int(df["average_salary"].dropna().max())
        salary_range = st.slider(
            "Average monthly salary",
            min_value=min_salary,
            max_value=max_salary,
            value=(min_salary, max_salary),
            step=500,
        )

        max_experience = int(df["minimumYearsExperience"].dropna().max())
        experience_range = st.slider(
            "Minimum years of experience",
            min_value=0,
            max_value=max_experience,
            value=(0, max_experience),
        )

    filtered = df.copy()

    if search_text:
        search_mask = (
            filtered["title"].fillna("").str.contains(search_text, case=False, regex=False)
            | filtered["postedCompany_name"].fillna("").str.contains(search_text, case=False, regex=False)
        )
        filtered = filtered[search_mask]

    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if selected_role_families:
        filtered = filtered[filtered["role_family"].isin(selected_role_families)]
    if selected_seniorities:
        filtered = filtered[filtered["seniority"].isin(selected_seniorities)]
    if selected_employment_types:
        filtered = filtered[filtered["employmentTypes"].isin(selected_employment_types)]

    filtered = filtered[
        filtered["average_salary"].between(salary_range[0], salary_range[1], inclusive="both")
        & filtered["minimumYearsExperience"].between(
            experience_range[0],
            experience_range[1],
            inclusive="both",
        )
    ]

    return filtered


def show_bar_chart(
    data: pd.DataFrame,
    label_column: str,
    value_column: str,
    title: str,
    y_axis_title: str,
    x_sort: list[str] | None = None,
    value_format: str | None = None,
) -> None:
    st.subheader(title)
    sort_order = x_sort if x_sort is not None else data[label_column].tolist()
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{label_column}:N",
                title=None,
                sort=sort_order,
                axis=alt.Axis(labelAngle=-30),
            ),
            y=alt.Y(f"{value_column}:Q", title=y_axis_title),
            tooltip=[
                alt.Tooltip(f"{label_column}:N", title=label_column.replace("_", " ").title()),
                alt.Tooltip(f"{value_column}:Q", title=y_axis_title, format=value_format),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(f"Vertical axis: {y_axis_title}.")


def main() -> None:
    st.title("Singapore Job Analytics")
    st.caption("A Pandas-powered dashboard for exploring Singapore job postings, salaries, demand, and career-switching signals.")

    try:
        csv_source = st.secrets.get("CSV_URL", DEFAULT_CSV_SOURCE)
    except FileNotFoundError:
        csv_source = DEFAULT_CSV_SOURCE

    if csv_source == DEFAULT_CSV_SOURCE and not PROCESSED_CSV_PATH.exists():
        csv_source = str(LOCAL_CSV_PATH)

    try:
        df = load_data(csv_source)
    except FileNotFoundError:
        st.error(
            "No dataset was found. Add data/singapore_jobs_processed.csv.gz, "
            "place the raw CSV at SGJobData.csv/SGJobData.csv, or add a CSV_URL "
            "value in Streamlit secrets."
        )
        st.stop()

    filtered = apply_filters(df)

    total_jobs = len(filtered)
    median_salary = filtered["average_salary"].median()
    median_experience = filtered["minimumYearsExperience"].median()
    total_applications = filtered["metadata_totalNumberJobApplication"].sum()

    metric_columns = st.columns(4)
    metric_columns[0].metric("Job postings", f"{total_jobs:,}")
    metric_columns[1].metric("Median salary", format_currency(median_salary))
    metric_columns[2].metric("Median experience", f"{median_experience:.1f} years" if pd.notna(median_experience) else "N/A")
    metric_columns[3].metric("Applications", f"{total_applications:,.0f}")

    if filtered.empty:
        st.warning("No jobs match the selected filters.")
        st.stop()

    tab_overview, tab_skills, tab_jobs = st.tabs(["Overview", "Skillsets", "Job Explorer"])

    with tab_overview:
        left, right = st.columns(2)

        role_counts = (
            filtered["role_family"]
            .value_counts()
            .head(10)
            .rename_axis("role_family")
            .reset_index(name="job_count")
        )
        with left:
            show_bar_chart(role_counts, "role_family", "job_count", "Top Career Tracks", "Number of job postings", value_format=",")

        salary_by_role = (
            filtered.groupby("role_family", as_index=False)["average_salary"]
            .median()
            .sort_values("average_salary", ascending=False)
            .head(10)
        )
        with right:
            show_bar_chart(
                salary_by_role,
                "role_family",
                "average_salary",
                "Median Salary by Career Track",
                "Median monthly salary (S$)",
                value_format=",.0f",
            )

        left, right = st.columns(2)

        seniority_counts = (
            filtered["seniority"]
            .value_counts()
            .reindex([level for level in SENIORITY_ORDER if level in filtered["seniority"].unique()])
            .dropna()
            .astype(int)
            .rename_axis("seniority")
            .reset_index(name="job_count")
        )
        with left:
            show_bar_chart(
                seniority_counts,
                "seniority",
                "job_count",
                "Jobs by Seniority",
                "Number of job postings",
                x_sort=SENIORITY_ORDER,
                value_format=",",
            )

        salary_by_seniority = (
            filtered.groupby("seniority", as_index=False)["average_salary"]
            .median()
            .assign(seniority=lambda data: pd.Categorical(data["seniority"], categories=SENIORITY_ORDER, ordered=True))
            .sort_values("seniority")
        )
        with right:
            show_bar_chart(
                salary_by_seniority,
                "seniority",
                "average_salary",
                "Median Salary by Seniority",
                "Median monthly salary (S$)",
                x_sort=SENIORITY_ORDER,
                value_format=",.0f",
            )

        category_counts = (
            filtered["category"]
            .value_counts()
            .head(12)
            .rename_axis("category")
            .reset_index(name="job_count")
        )
        show_bar_chart(category_counts, "category", "job_count", "Top Industry / Job Categories", "Number of job postings", value_format=",")

    with tab_skills:
        skill_rows = filtered.explode("skill_signals")
        skill_rows = skill_rows[skill_rows["skill_signals"].notna()]

        if skill_rows.empty:
            st.info("No title-based skillsets found for the selected filters.")
        else:
            left, right = st.columns(2)

            skill_counts = (
                skill_rows["skill_signals"]
                .value_counts()
                .head(15)
                .rename_axis("skill")
                .reset_index(name="job_count")
            )
            with left:
                show_bar_chart(skill_counts, "skill", "job_count", "Most Visible Skillsets", "Number of job postings", value_format=",")

            skill_salary = (
                skill_rows.groupby("skill_signals", as_index=False)["average_salary"]
                .median()
                .sort_values("average_salary", ascending=False)
                .head(15)
                .rename(columns={"skill_signals": "skill"})
            )
            with right:
                show_bar_chart(
                    skill_salary,
                    "skill",
                    "average_salary",
                    "Median Salary by Skillset",
                    "Median monthly salary (S$)",
                    value_format=",.0f",
                )

            st.dataframe(
                skill_counts.merge(skill_salary, on="skill", how="left").rename(
                    columns={"skill": "Skillset", "job_count": "Job Count", "average_salary": "Median Salary"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_jobs:
        display_columns = [
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
            "metadata_totalNumberJobApplication",
            "metadata_totalNumberOfView",
        ]
        st.dataframe(
            filtered[display_columns]
            .sort_values("average_salary", ascending=False)
            .rename(columns={
                "postedCompany_name": "company",
                "category": "industry_job_category",
                "role_family": "career_track",
            }),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
