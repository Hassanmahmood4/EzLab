// LabPulse Typst report template — expects resolved_report.json beside this compile cwd.
#set page(margin: 2cm)
#set text(size: 11pt)
#set heading(numbering: "1.")

#let data = json("resolved_report.json")
#let cover = data.cover_page
#let body = data.report_body
#let anomaly = data.anomaly_check

#align(center)[
  #if data.university_logo_path != "" [
    #image(data.university_logo_path, width: 2.4cm)
  ]
  #v(0.4cm)
  #text(16pt, weight: "bold")[#data.university_full_name]
  #v(0.2cm)
  #text(12pt)[#cover.department]
  #v(0.6cm)
  #text(14pt, weight: "bold")[#cover.lab_number — #cover.experiment_title]
]

#v(0.8cm)

#grid(
  columns: (auto, 1fr),
  row-gutter: 0.35em,
  column-gutter: 0.8em,
  [*Course:*], [#cover.course_code — #cover.course_title],
  [*Student:*], [#cover.student_name],
  [*Registration No:*], [#cover.registration_no],
  [*Section:*], [#cover.section],
  [*Instructor:*], [#cover.instructor],
  [*Date:*], [#cover.submission_date],
)

#pagebreak()

= Abstract
#body.abstract

= Apparatus / Tools
#for item in body.apparatus [
  - #item
]

= Methodology
#body.methodology

= Equations
#for eq in body.equations_latex [
  #block(width: 100%, inset: 0.4em)[
    #set align(center)
    #raw(eq)
  ]
]

= Anomaly Check
*Status:* #anomaly.status

#if anomaly.flags.len() == 0 [
  No anomalies flagged.
] else [
  #for flag in anomaly.flags [
    - #flag
  ]
]

= Results
#for tbl in body.tables [
  #block(width: 100%, spacing: 1em)[
    #emph[#tbl.caption]
    #table(
      columns: tbl.headers.len(),
      stroke: 0.5pt + luma(180),
      inset: 6pt,
      ..tbl.headers.map(h => strong(h)),
      ..tbl.rows.map(row => row.map(cell => [#cell])).flatten(),
    )
  ]
]

= Figure
#if data.plot_path != "" [
  #align(center)[
    #image(data.plot_path, width: 80%)
  ]
]

= Discussion
#body.discussion

= Conclusion
#body.conclusion
