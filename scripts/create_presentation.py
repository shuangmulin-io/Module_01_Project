from __future__ import annotations

import html
import shutil
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "singapore_jobs_processed.csv.gz"
OUT_DIR = ROOT / "presentation"
ASSET_DIR = OUT_DIR / "assets"
PPTX_PATH = OUT_DIR / "Singapore_Job_Analytics_10min_Presentation.pptx"
SCRIPT_PATH = OUT_DIR / "Singapore_Job_Analytics_speaker_script.md"

SLIDE_W = 12_192_000
SLIDE_H = 6_858_000
EMU = 914_400

NAVY = "17324D"
TEAL = "1F7A8C"
CORAL = "E26D5A"
GOLD = "F2B134"
MINT = "8BC6A6"
INK = "1F2933"
MUTED = "667085"
LIGHT = "F6F8FA"
WHITE = "FFFFFF"


def emu(inches: float) -> int:
    return int(inches * EMU)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_int(value: float | int) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}"


def money(value: float | int) -> str:
    if pd.isna(value):
        return "N/A"
    return f"S${int(round(value)):,}"


def clean_dirs() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    if ASSET_DIR.exists():
        shutil.rmtree(ASSET_DIR)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    for col in ["average_salary", "minimumYearsExperience", "numberOfVacancies", "metadata_totalNumberJobApplication", "metadata_totalNumberOfView"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["metadata_newPostingDate"] = pd.to_datetime(df["metadata_newPostingDate"], errors="coerce")
    return df


def bar_chart(data: pd.DataFrame, label: str, value: str, title: str, path: Path, color: str = f"#{TEAL}") -> None:
    plot_data = data.copy()
    plot_data[label] = plot_data[label].astype(str)
    fig_h = max(4.2, 0.35 * len(plot_data) + 1.1)
    fig, ax = plt.subplots(figsize=(8.6, fig_h), dpi=180)
    ax.barh(plot_data[label][::-1], plot_data[value][::-1], color=color)
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=f"#{INK}", pad=12)
    ax.tick_params(axis="x", labelsize=9, colors=f"#{MUTED}")
    ax.tick_params(axis="y", labelsize=9, colors=f"#{INK}")
    ax.grid(axis="x", color="#D7DEE8", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    max_v = plot_data[value].max()
    for i, v in enumerate(plot_data[value][::-1]):
        ax.text(v + max_v * 0.015, i, safe_int(v), va="center", fontsize=8.5, color=f"#{MUTED}")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_charts(df: pd.DataFrame) -> dict[str, Path]:
    charts: dict[str, Path] = {}
    top_categories = df["category"].value_counts().head(10).rename_axis("category").reset_index(name="job_count")
    charts["categories"] = ASSET_DIR / "top_categories.png"
    bar_chart(top_categories, "category", "job_count", "Top industry / job categories", charts["categories"], f"#{TEAL}")

    role_counts = df["role_family"].value_counts().head(8).rename_axis("role_family").reset_index(name="job_count")
    charts["roles"] = ASSET_DIR / "top_role_families.png"
    bar_chart(role_counts, "role_family", "job_count", "Most common career tracks", charts["roles"], f"#{CORAL}")

    salary_role = (
        df.groupby("role_family", as_index=False)["average_salary"]
        .median()
        .dropna()
        .sort_values("average_salary", ascending=False)
        .head(8)
    )
    charts["salary_role"] = ASSET_DIR / "salary_by_role.png"
    bar_chart(salary_role, "role_family", "average_salary", "Median monthly salary by track", charts["salary_role"], f"#{GOLD}")

    skill_rows = df.dropna(subset=["skill_signals"]).copy()
    skill_rows["skill_signals"] = skill_rows["skill_signals"].astype(str).str.split(",")
    skill_rows = skill_rows.explode("skill_signals")
    skill_rows["skill_signals"] = skill_rows["skill_signals"].astype(str).str.strip()
    skill_rows = skill_rows[skill_rows["skill_signals"] != ""]
    skill_counts = skill_rows["skill_signals"].value_counts().head(10).rename_axis("skill").reset_index(name="job_count")
    charts["skills"] = ASSET_DIR / "skill_signals.png"
    bar_chart(skill_counts, "skill", "job_count", "Visible skill signals from job titles", charts["skills"], f"#{MINT}")

    return charts


def tx_body(lines: list[str], font_size: int = 24, color: str = INK, bullet: bool = False, bold_first: bool = False) -> str:
    paragraphs = []
    for idx, line in enumerate(lines):
        bullet_xml = ""
        if bullet:
            bullet_xml = '<a:pPr marL="285750" indent="-171450"><a:buChar char="•"/></a:pPr>'
        else:
            bullet_xml = '<a:pPr/>'
        bold = ' b="1"' if bold_first and idx == 0 else ""
        paragraphs.append(
            f"<a:p>{bullet_xml}<a:r><a:rPr lang=\"en-US\" sz=\"{font_size * 100}\"{bold}>"
            f"<a:solidFill><a:srgbClr val=\"{color}\"/></a:solidFill></a:rPr><a:t>{esc(line)}</a:t></a:r></a:p>"
        )
    return "<p:txBody><a:bodyPr wrap=\"square\"/><a:lstStyle/>" + "".join(paragraphs) + "</p:txBody>"


def shape_text(x: float, y: float, w: float, h: float, lines: list[str], font_size: int = 24, color: str = INK,
               fill: str | None = None, bullet: bool = False, bold_first: bool = False, name: str = "Text") -> str:
    fill_xml = "<a:noFill/>" if fill is None else f"<a:solidFill><a:srgbClr val=\"{fill}\"/></a:solidFill>"
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id=\"{shape_text.next_id}\" name=\"{esc(name)}\"/><p:cNvSpPr txBox=\"1\"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x=\"{emu(x)}\" y=\"{emu(y)}\"/><a:ext cx=\"{emu(w)}\" cy=\"{emu(h)}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>
      {tx_body(lines, font_size, color, bullet, bold_first)}
    </p:sp>
    """


shape_text.next_id = 10


def rect(x: float, y: float, w: float, h: float, fill: str, name: str = "Rectangle") -> str:
    shape_text.next_id += 1
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id=\"{shape_text.next_id}\" name=\"{esc(name)}\"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x=\"{emu(x)}\" y=\"{emu(y)}\"/><a:ext cx=\"{emu(w)}\" cy=\"{emu(h)}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val=\"{fill}\"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>
    </p:sp>
    """


def image_pic(rid: str, x: float, y: float, w: float, h: float, name: str) -> str:
    shape_text.next_id += 1
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id=\"{shape_text.next_id}\" name=\"{esc(name)}\"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed=\"{rid}\"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x=\"{emu(x)}\" y=\"{emu(y)}\"/><a:ext cx=\"{emu(w)}\" cy=\"{emu(h)}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
    """


def slide_xml(elements: list[str], bg: str = WHITE) -> str:
    shape_text.next_id = 10
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<p:sld xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val=\"{bg}\"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/><a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>
      {''.join(elements)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def slide_rels(images: list[tuple[str, str]]) -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    ]
    for idx, (_, target) in enumerate(images, start=2):
        rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{esc(target)}"/>'
        )
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(rels) + "</Relationships>"


def add_title(title: str, subtitle: str | None = None) -> list[str]:
    elements = [shape_text(0.55, 0.35, 11.3, 0.55, [title], 30, NAVY, bold_first=True)]
    if subtitle:
        elements.append(shape_text(0.58, 0.92, 10.8, 0.35, [subtitle], 14, MUTED))
    elements.append(rect(0.58, 1.22, 1.2, 0.05, CORAL))
    return elements


def metric_card(x: float, y: float, w: float, label: str, value: str, color: str) -> list[str]:
    return [
        rect(x, y, w, 0.95, LIGHT),
        shape_text(x + 0.18, y + 0.12, w - 0.35, 0.25, [label], 11, MUTED),
        shape_text(x + 0.18, y + 0.42, w - 0.35, 0.35, [value], 22, color, bold_first=True),
    ]


def build_slides(df: pd.DataFrame, charts: dict[str, Path]) -> tuple[list[dict], list[Path]]:
    image_files: list[Path] = []
    date_min = df["metadata_newPostingDate"].min()
    date_max = df["metadata_newPostingDate"].max()
    stats = {
        "jobs": safe_int(len(df)),
        "median_salary": money(df["average_salary"].median()),
        "median_exp": f"{df['minimumYearsExperience'].median():.1f} yrs",
        "apps": safe_int(df["metadata_totalNumberJobApplication"].sum()),
        "views": safe_int(df["metadata_totalNumberOfView"].sum()),
        "period": f"{date_min:%b %Y} to {date_max:%b %Y}" if pd.notna(date_min) and pd.notna(date_max) else "Available posting dates",
        "categories": safe_int(df["category"].nunique()),
        "roles": safe_int(df["role_family"].nunique()),
    }

    slides: list[dict] = []

    slides.append({
        "title": "Title",
        "elements": [
            rect(0, 0, 12.0, 7.5, NAVY),
            rect(0, 5.55, 12.0, 1.95, TEAL),
            shape_text(0.72, 1.15, 10.8, 1.1, ["Singapore Job Analytics"], 42, WHITE, bold_first=True),
            shape_text(0.75, 2.34, 10.4, 0.6, ["A dashboard for jobseekers and career switchers"], 24, "D8EEF2"),
            shape_text(0.78, 5.92, 9.8, 0.55, ["10-minute project presentation"], 22, WHITE),
            shape_text(0.78, 6.43, 9.8, 0.35, ["Dataset-driven view of demand, salary, accessibility, and skill signals"], 14, "EAF7F8"),
        ],
        "images": [],
    })

    elements = add_title("1. Why This Project Matters", "The dashboard is built around career decisions, not just data exploration.")
    elements += [
        shape_text(0.75, 1.55, 5.2, 0.5, ["Core audience"], 20, NAVY, bold_first=True),
        shape_text(0.95, 2.05, 4.85, 1.45, [
            "Singapore-based jobseekers",
            "Career switchers comparing pathways",
            "Students or fresh graduates planning first roles",
        ], 18, INK, bullet=True),
        shape_text(6.35, 1.55, 5.0, 0.5, ["Decision it supports"], 20, NAVY, bold_first=True),
        shape_text(6.55, 2.05, 4.9, 1.65, [
            "Which sectors are hiring?",
            "Which roles are accessible?",
            "What salary range can I expect?",
            "Which visible skill signals appear in job titles?",
        ], 18, INK, bullet=True),
        shape_text(1.0, 4.55, 10.4, 0.75, ["Main question: Which roles and skillsets should I consider to improve employability?"], 24, CORAL, bold_first=True),
    ]
    slides.append({"title": "Why", "elements": elements, "images": []})

    elements = add_title("2. Data Foundation", "The CSV turns advertised job postings into measurable career signals.")
    elements += metric_card(0.72, 1.62, 2.55, "Processed postings", stats["jobs"], TEAL)
    elements += metric_card(3.55, 1.62, 2.35, "Period", stats["period"], CORAL)
    elements += metric_card(6.18, 1.62, 2.15, "Categories", stats["categories"], GOLD)
    elements += metric_card(8.62, 1.62, 2.55, "Career tracks", stats["roles"], MINT)
    elements += [
        shape_text(0.82, 3.1, 10.8, 0.45, ["Important fields used in the dashboard"], 20, NAVY, bold_first=True),
        shape_text(1.02, 3.65, 10.15, 1.35, [
            "title: advertised position or role name",
            "category: industry or job-function area",
            "salary and experience: market expectation and accessibility",
            "applications and views: rough interest or competition signals",
            "position level and title keywords: seniority, career track, and visible skill signals",
        ], 16, INK, bullet=True),
        shape_text(0.96, 5.55, 10.6, 0.55, ["A job title is specific; a category gives the wider labour-market context."], 21, CORAL, bold_first=True),
    ]
    slides.append({"title": "Data", "elements": elements, "images": []})

    elements = add_title("3. From Raw CSV to Dashboard Metrics", "The analysis converts posting fields into jobseeker-friendly views.")
    elements += [
        rect(0.88, 1.75, 2.1, 1.05, LIGHT),
        shape_text(1.05, 2.02, 1.75, 0.35, ["Raw postings"], 20, NAVY, bold_first=True),
        rect(3.65, 1.75, 2.2, 1.05, LIGHT),
        shape_text(3.82, 1.96, 1.9, 0.48, ["Clean & classify"], 18, NAVY, bold_first=True),
        rect(6.52, 1.75, 2.15, 1.05, LIGHT),
        shape_text(6.72, 1.96, 1.75, 0.48, ["Aggregate metrics"], 18, NAVY, bold_first=True),
        rect(9.25, 1.75, 2.25, 1.05, LIGHT),
        shape_text(9.42, 1.96, 1.9, 0.48, ["Interactive filters"], 18, NAVY, bold_first=True),
        shape_text(3.12, 2.04, 0.32, 0.35, ["→"], 24, CORAL),
        shape_text(5.98, 2.04, 0.32, 0.35, ["→"], 24, CORAL),
        shape_text(8.78, 2.04, 0.32, 0.35, ["→"], 24, CORAL),
        shape_text(1.0, 3.55, 10.3, 1.55, [
            "Primary category is extracted from the category list.",
            "Role family is classified from title keywords.",
            "Seniority is inferred from position level, title, and minimum experience.",
            "Skillsets are title-based signals, such as SQL, Python, Excel, Java, sales, or analytics.",
        ], 17, INK, bullet=True),
    ]
    slides.append({"title": "Method", "elements": elements, "images": []})

    image_files.append(charts["categories"])
    elements = add_title("4. Market Demand by Category", "Categories show the broad sectors and functions with the most advertised activity.")
    elements += [image_pic("rId2", 0.72, 1.45, 6.2, 4.75, "Top categories")]
    elements += [
        shape_text(7.22, 1.7, 4.35, 0.5, ["How to interpret this"], 21, NAVY, bold_first=True),
        shape_text(7.38, 2.25, 4.05, 1.8, [
            "High count means more advertised openings.",
            "Categories help jobseekers compare broad career areas.",
            "A role can appear across sectors, so category and title should be analysed together.",
        ], 17, INK, bullet=True),
        shape_text(7.35, 4.7, 4.05, 0.8, ["Jobseeker takeaway: start with active sectors, then inspect the actual titles inside them."], 19, CORAL, bold_first=True),
    ]
    slides.append({"title": "Categories", "elements": elements, "images": [charts["categories"]]})

    image_files.append(charts["roles"])
    elements = add_title("5. Role Families Translate Titles into Career Tracks", "Job titles are messy, so the dashboard groups them into clearer pathways.")
    elements += [image_pic("rId2", 0.68, 1.42, 6.25, 4.85, "Role families")]
    elements += [
        shape_text(7.25, 1.62, 4.3, 0.5, ["Why this matters"], 21, NAVY, bold_first=True),
        shape_text(7.43, 2.16, 4.05, 1.7, [
            "Titles answer: What job is advertised?",
            "Role families answer: What career track does it belong to?",
            "This helps users discover alternative titles they may not have searched for.",
        ], 17, INK, bullet=True),
        shape_text(7.35, 4.6, 4.0, 0.95, ["Example: analyst, data analyst, BI analyst, and reporting analyst can be viewed as related pathways."], 18, CORAL),
    ]
    slides.append({"title": "Roles", "elements": elements, "images": [charts["roles"]]})

    image_files.append(charts["salary_role"])
    elements = add_title("6. Salary and Accessibility", "Salary becomes more useful when combined with experience and seniority.")
    elements += [image_pic("rId2", 0.72, 1.42, 6.2, 4.8, "Salary by role")]
    elements += metric_card(7.24, 1.62, 3.85, "Median monthly salary", stats["median_salary"], GOLD)
    elements += metric_card(7.24, 2.82, 3.85, "Median required experience", stats["median_exp"], TEAL)
    elements += [
        shape_text(7.35, 4.35, 4.0, 1.1, [
            "A high-paying role may not be realistic for an entry-level switcher.",
            "A moderate salary with low experience requirements may be a better first target.",
        ], 16, INK, bullet=True),
    ]
    slides.append({"title": "Salary", "elements": elements, "images": [charts["salary_role"]]})

    image_files.append(charts["skills"])
    elements = add_title("7. Skillset Signals", "The dashboard can suggest visible skill signals, but it cannot fully replace job descriptions.")
    elements += [image_pic("rId2", 0.72, 1.42, 6.15, 4.75, "Skill signals")]
    elements += [
        shape_text(7.18, 1.58, 4.35, 0.5, ["What this can say"], 21, NAVY, bold_first=True),
        shape_text(7.38, 2.12, 4.1, 1.15, [
            "Skills visible in job titles can highlight role direction.",
            "Examples include SQL, Python, Excel, Java, sales, finance, and analytics.",
        ], 16, INK, bullet=True),
        shape_text(7.18, 3.72, 4.35, 0.5, ["Important limitation"], 21, CORAL, bold_first=True),
        shape_text(7.38, 4.28, 4.1, 1.0, [
            "The CSV does not include full job descriptions.",
            "So skill counts are signals, not complete skill requirements.",
        ], 16, INK, bullet=True),
    ]
    slides.append({"title": "Skills", "elements": elements, "images": [charts["skills"]]})

    elements = add_title("8. Who Else Benefits?", "The same dataset can support different dashboard designs for different decisions.")
    rows = [
        ("Training providers", "Course planning", "High-demand role families, visible skill signals, salary outcomes"),
        ("Employers / HR", "Hiring competitiveness", "Salary benchmark, applications, views, similar postings"),
        ("Policy teams", "Labour-market planning", "Sector demand, entry-level access, high-demand/low-application gaps"),
        ("Career coaches", "Guidance conversations", "Alternative titles, accessible roles, salary and competition signals"),
    ]
    y = 1.55
    for audience, decision, metrics in rows:
        elements += [rect(0.75, y, 10.75, 0.78, LIGHT)]
        elements += [shape_text(0.95, y + 0.14, 2.25, 0.28, [audience], 15, NAVY, bold_first=True)]
        elements += [shape_text(3.45, y + 0.14, 2.0, 0.28, [decision], 14, CORAL)]
        elements += [shape_text(5.75, y + 0.14, 5.35, 0.28, [metrics], 13, INK)]
        y += 0.95
    elements += [shape_text(0.88, 5.7, 10.4, 0.48, ["Design principle: each audience needs different metrics because each audience has a different decision to make."], 19, TEAL, bold_first=True)]
    slides.append({"title": "Audiences", "elements": elements, "images": []})

    elements = add_title("9. Conclusion and Next Steps", "The dashboard is useful now, and stronger with richer job-description data.")
    elements += [
        shape_text(0.85, 1.55, 5.1, 0.45, ["What the project delivers"], 21, NAVY, bold_first=True),
        shape_text(1.05, 2.1, 4.75, 1.7, [
            "Career exploration by sector, role family, seniority, salary, and experience",
            "Job explorer for comparing real advertised positions",
            "Title-based skill signals for early career planning",
        ], 17, INK, bullet=True),
        shape_text(6.35, 1.55, 4.9, 0.45, ["Recommended improvements"], 21, NAVY, bold_first=True),
        shape_text(6.55, 2.1, 4.75, 1.95, [
            "Add full job descriptions for stronger skill extraction",
            "Map role titles to a formal skills taxonomy",
            "Track trends over time and separate active vs closed postings",
            "Add role pathway recommendations for career switchers",
        ], 17, INK, bullet=True),
        shape_text(1.0, 5.35, 10.2, 0.7, ["Final message: the dashboard helps users move from “What jobs exist?” to “Which career direction should I explore next?”"], 22, CORAL, bold_first=True),
    ]
    slides.append({"title": "Conclusion", "elements": elements, "images": []})

    return slides, image_files


def static_files(slide_count: int) -> dict[str, str]:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, slide_count + 1):
        overrides.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        + "".join(overrides) + "</Types>"
    )

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )

    slide_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, slide_count + 1))
    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    pres_rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, slide_count + 1):
        pres_rels.append(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
    presentation_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(pres_rels) + "</Relationships>"

    master = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""

    master_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
        '</Relationships>'
    )

    layout = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""

    layout_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
        '</Relationships>'
    )

    theme = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Singapore Job Analytics">
  <a:themeElements>
    <a:clrScheme name="Custom"><a:dk1><a:srgbClr val="{INK}"/></a:dk1><a:lt1><a:srgbClr val="{WHITE}"/></a:lt1><a:dk2><a:srgbClr val="{NAVY}"/></a:dk2><a:lt2><a:srgbClr val="{LIGHT}"/></a:lt2><a:accent1><a:srgbClr val="{TEAL}"/></a:accent1><a:accent2><a:srgbClr val="{CORAL}"/></a:accent2><a:accent3><a:srgbClr val="{GOLD}"/></a:accent3><a:accent4><a:srgbClr val="{MINT}"/></a:accent4><a:accent5><a:srgbClr val="576CBC"/></a:accent5><a:accent6><a:srgbClr val="7D5A50"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Simple"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>"""

    app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex</Application><PresentationFormat>On-screen Show (16:9)</PresentationFormat></Properties>"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Singapore Job Analytics 10-minute Presentation</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy></cp:coreProperties>"""

    return {
        "[Content_Types].xml": content_types,
        "_rels/.rels": root_rels,
        "ppt/presentation.xml": presentation,
        "ppt/_rels/presentation.xml.rels": presentation_rels,
        "ppt/slideMasters/slideMaster1.xml": master,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": master_rels,
        "ppt/slideLayouts/slideLayout1.xml": layout,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": layout_rels,
        "ppt/theme/theme1.xml": theme,
        "docProps/app.xml": app,
        "docProps/core.xml": core,
    }


def create_pptx(slides: list[dict]) -> None:
    media_map: dict[Path, str] = {}
    media_counter = 1
    with zipfile.ZipFile(PPTX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in static_files(len(slides)).items():
            z.writestr(name, content)
        for idx, slide in enumerate(slides, start=1):
            rel_images: list[tuple[Path, str]] = []
            for image in slide["images"]:
                image = Path(image)
                if image not in media_map:
                    media_name = f"image{media_counter}.png"
                    media_map[image] = media_name
                    z.write(image, f"ppt/media/{media_name}")
                    media_counter += 1
                rel_images.append((image, media_map[image]))
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(slide["elements"]))
            z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels(rel_images))


def create_script(df: pd.DataFrame) -> None:
    script = f"""# Singapore Job Analytics - 10 Minute Speaker Script

## Slide 1 - Title
Good afternoon. My project is Singapore Job Analytics, a dashboard designed to help jobseekers and career switchers understand the Singapore job market through advertised job postings.

## Slide 2 - Why this project matters
The target audience is people making career decisions: jobseekers, career switchers, students, and fresh graduates. The dashboard helps them compare sectors, roles, salary expectations, experience requirements, and visible skill signals.

## Slide 3 - Data foundation
The processed dashboard dataset contains {safe_int(len(df))} job postings. The most important fields are job title, category, salary range, minimum years of experience, applications, views, and position level. Title tells us the advertised role; category tells us the broader sector or function.

## Slide 4 - Method
The raw CSV is cleaned and transformed into dashboard metrics. The project extracts a primary category, classifies role families from title keywords, estimates seniority using title, position level, and experience, then identifies title-based skill signals.

## Slide 5 - Market demand by category
This view shows which categories have the most advertised job activity. For jobseekers, category helps answer which sectors are active. But category alone is not enough, because the same role can appear in different sectors.

## Slide 6 - Role families
Role families make job titles easier to compare. Instead of treating every title as unrelated, similar titles are grouped into tracks such as Software & Engineering, Data & Analytics, Finance & Accounting, Sales & Marketing, and Operations & Supply Chain.

## Slide 7 - Salary and accessibility
Salary is useful, but only when combined with experience and seniority. A high-paying role may require more years of experience, while a lower-entry role may be a more realistic first step for a career switcher.

## Slide 8 - Skillset signals
The dashboard can identify visible skills from job titles, such as Python, SQL, Excel, Java, sales, finance, or analytics. However, the CSV does not include full job descriptions, so the skill metrics should be described as signals, not complete skill requirements.

## Slide 9 - Other audiences
The same data can also help training providers plan courses, employers benchmark salaries, workforce policy teams study labour-market demand, and career coaches recommend alternative pathways.

## Slide 10 - Conclusion
The main value of the dashboard is that it helps users move from “what jobs exist?” to “which career direction should I explore next?” Future improvements would include full job descriptions, a formal skill taxonomy, trend analysis, and stronger pathway recommendations.
"""
    SCRIPT_PATH.write_text(script, encoding="utf-8")


def main() -> None:
    clean_dirs()
    df = load_data()
    charts = create_charts(df)
    slides, _ = build_slides(df, charts)
    create_pptx(slides)
    create_script(df)
    print(PPTX_PATH)
    print(SCRIPT_PATH)


if __name__ == "__main__":
    main()
