# Singapore Job Analytics - 10 Minute Speaker Script

## Slide 1 - Title
Good afternoon. My project is Singapore Job Analytics, a dashboard designed to help jobseekers and career switchers understand the Singapore job market through advertised job postings.

## Slide 2 - Why this project matters
The target audience is people making career decisions: jobseekers, career switchers, students, and fresh graduates. The dashboard helps them compare sectors, roles, salary expectations, experience requirements, and visible skill signals.

## Slide 3 - Data foundation
The processed dashboard dataset contains 1,036,725 job postings. The most important fields are job title, category, salary range, minimum years of experience, applications, views, and position level. Title tells us the advertised role; category tells us the broader sector or function.

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
