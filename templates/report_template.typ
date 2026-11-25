// EzLab — task / code / output lab report (A4)
#let data = json("resolved_report.json")
#let cover = data.cover_page
#let tasks = data.tasks

#let navy = rgb("#1a2744")
#let rule = rgb("#c5cad3")
#let mute = rgb("#5c6478")
#let soft = rgb("#f4f6f9")
#let border-inset = 0.9cm

#set page(
  paper: "a4",
  margin: (top: 1.7cm, bottom: 1.7cm, left: 1.7cm, right: 1.7cm),
  foreground: context {
    place(
      top + left,
      dx: border-inset,
      dy: border-inset,
      rect(
        width: page.width - 2 * border-inset,
        height: page.height - 2 * border-inset,
        stroke: 1.15pt + navy,
        fill: none,
      ),
    )
  },
  footer: context {
    if counter(page).get().first() > 1 [
      #align(center)[
        #set text(8.5pt, fill: mute)
        #counter(page).display()
      ]
    ]
  },
)

#set text(font: ("New Computer Modern", "Libertinus Serif", "Times New Roman"), size: 11pt, fill: navy.lighten(8%))
#set par(justify: true, leading: 0.75em, spacing: 0.85em)

#let mono-block(label, body) = {
  v(0.45em)
  text(11pt, weight: "bold", fill: navy)[#label]
  v(0.2em)
  block(
    width: 100%,
    inset: 0.65em,
    fill: soft,
    stroke: 0.55pt + rule,
    radius: 2pt,
    breakable: true,
  )[
    #set text(8.5pt, font: ("SF Mono", "Menlo", "Consolas", "Courier New"), fill: navy)
    #set par(justify: false, leading: 0.65em)
    #raw(body, block: true)
  ]
}

// ── Cover ────────────────────────────────────────────────────
#align(center)[
  #if data.university_logo_path != "" [
    #image(data.university_logo_path, width: 10cm)
    #v(0.25cm)
  ]
  #text(14pt, weight: "bold", fill: navy)[#data.university_full_name]
  #v(0.45cm)
  #text(12pt, weight: "bold", fill: navy)[LAB REPORT]
  #v(0.25cm)
  #text(12pt, weight: "bold", fill: navy)[#cover.lab_number: #cover.experiment_title]
  #v(0.35cm)
  #text(11pt)[Course: #cover.course_code — #cover.course_title]
  #v(0.15cm)
  #text(11pt)[Department: #cover.department]
  #if cover.section != "" [
    #v(0.15cm)
    #text(11pt)[Section: #cover.section]
  ]
  #if cover.at("semester", default: "") != "" [
    #v(0.15cm)
    #text(11pt)[Semester: #cover.semester]
  ]
  #v(0.45cm)
  #text(11pt)[Submitted By: #cover.student_name]
  #v(0.15cm)
  #text(11pt)[Registration No.: #cover.registration_no]
  #v(0.15cm)
  #text(11pt)[Lab Instructor: #cover.instructor]
  #v(0.15cm)
  #text(11pt)[Submission Date: #cover.submission_date]
]

#pagebreak()

// ── Tasks ────────────────────────────────────────────────────
#for task in tasks [
  #block(breakable: false)[
    #text(13pt, weight: "bold", fill: navy)[Task #task.number — #task.title]
    #v(0.35em)
    #if task.prompt != "" [
      #set text(11pt)
      #task.prompt
      #v(0.35em)
    ]
  ]
  #mono-block("Code", task.code)
  #mono-block("Output", if task.output != "" { task.output } else { "(none)" })
  #if task.at("figures", default: ()).len() > 0 [
    #v(0.55em)
    #text(11pt, weight: "bold", fill: navy)[Visualization Output]
    #v(0.3em)
    #for fig in task.figures [
      #align(center)[
        #block(
          width: 100%,
          inset: 0.4em,
          stroke: 0.55pt + rule,
          radius: 2pt,
          fill: white,
        )[
          #image(fig, width: 92%)
        ]
      ]
      #v(0.45em)
    ]
  ]
  #v(1.0em)
]
