#!/usr/bin/env python3
"""Generate CS-focused synthetic lab report chat pairs for LabPulse LoRA training."""

from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.schema import SYSTEM_PROMPT, LabReportSchema  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent
UNIVERSITIES_PATH = ROOT / "assets" / "universities.json"

SAMPLES_PER_SUBJECT = 70  # 16 * 70 = 1120 total
TRAIN_N = 850
VALID_N = 100
# remainder → test
SEED = 42

FIRST_NAMES = [
    "Hassan", "Ayesha", "Ali", "Fatima", "Bilal", "Sara", "Usman", "Hira",
    "Omar", "Zainab", "Ahmed", "Noor", "Hamza", "Maryam", "Saad", "Iqra",
    "Daniyal", "Laiba", "Taha", "Areeba", "Raza", "Maham", "Faisal", "Sana",
]
LAST_NAMES = [
    "Ali", "Khan", "Ahmed", "Hussain", "Malik", "Raza", "Iqbal", "Sheikh",
    "Butt", "Qureshi", "Mirza", "Siddiqui", "Chaudhry", "Shah", "Rehman", "Baig",
]
INSTRUCTORS = [
    "Dr. Ayesha Khan", "Dr. Imran Malik", "Dr. Sana Qureshi", "Dr. Bilal Hussain",
    "Mr. Usman Ali", "Ms. Hira Sheikh", "Dr. Farhan Raza", "Dr. Nadia Ahmed",
]
DEPARTMENTS = [
    "Department of Computer Science",
    "Department of Software Engineering",
    "Department of Information Technology",
    "School of Computing",
]
SECTIONS = ["BCS-2A", "BCS-2B", "BCS-4A", "BSE-4B", "BIT-6A", "BCS-6B", "BSSE-3A"]

# Noisy aliases → canonical university_id
UNIVERSITY_ALIASES: dict[str, list[str]] = {
    "nust": ["SEECS NUST", "NUST SEECS", "NUST Islamabad", "NUST H-12"],
    "fast_nuces": ["FAST-NU Isb", "FAST NUCES", "FAST Islamabad", "NUCES FAST"],
    "comsats": ["CUI Wah", "COMSATS Isb", "CUI Islamabad", "COMSATS"],
    "uet_lahore": ["UET LHR", "UET Lahore", "UET Main"],
    "giki": ["GIK Topi", "GIKI", "GIK Institute"],
    "pieas": ["PIEAS Isb", "PIEAS"],
    "lums": ["LUMS Lhr", "LUMS", "SBASSE LUMS"],
    "ned": ["NED UET", "NED Karachi", "NED University"],
    "air_university": ["Air Uni", "AU Islamabad", "Air University"],
    "itu": ["ITU Lhr", "ITU Lahore", "Arfa ITU"],
    "qau": ["QAU Isb", "Quaid-i-Azam", "QAU"],
    "pu": ["PUCIT", "Punjab Uni", "PU Lahore", "PU Old Campus"],
    "pak_austria": ["Pak Austria", "PAF-IAST", "Pak-Austria Haripur", "PAFIAST", "Pak Austria Uni"],
    "bahria": ["Bahria Uni", "BUKC", "Bahria Islamabad", "Bahria University", "BUIC"],
    "iiui": ["IIUI", "Islamic Uni Isb", "Intl Islamic University", "IIU Islamabad", "Islamic University"],
    "numl": ["NUML Isb", "NUML", "NUML Islamabad", "National Uni Modern Languages"],
    "szabist": ["SZABIST", "SZABIST Isb", "SZABIST Karachi", "Shaheed Zulfikar Ali Bhutto IST"],
    "iba": ["IBA Khi", "IBA Karachi", "IBA", "IBA City Campus"],
    "riphah": ["Riphah", "Riphah Isb", "RIU", "Riphah International"],
    "uet_taxila": ["UET Taxila", "UETT", "Taxila UET", "UET TXL"],
}


@dataclass
class SubjectSpec:
    key: str
    course_code: str
    course_title: str
    experiments: list[str]


SUBJECTS: list[SubjectSpec] = [
    SubjectSpec("pf", "CS-100", "Programming Fundamentals Lab", [
        "Loop Runtime Profiling with Nested Iterations",
        "Array Search Linear vs Binary Timing Study",
        "Factorial Recursion vs Iteration Benchmark",
        "String Manipulation Throughput Lab",
    ]),
    SubjectSpec("oop", "CS-212", "Object-Oriented Programming Lab", [
        "Inheritance Hierarchy Unit-Test Coverage",
        "Polymorphism Dispatcher Benchmark",
        "Encapsulation & Getter Overhead Study",
        "Exception Handling Path Coverage Lab",
    ]),
    SubjectSpec("ds", "CS-218", "Data Structures Lab", [
        "Stack vs Queue Operation Throughput",
        "Linked List vs ArrayList Insertion Cost",
        "BST Search vs Hash Table Lookup",
        "Heap Insert/Extract Timing Analysis",
    ]),
    SubjectSpec("algo", "CS-302", "Design and Analysis of Algorithms Lab", [
        "Empirical Runtime Comparison of MergeSort and QuickSort",
        "Dijkstra vs Bellman-Ford Pathfinding Cost",
        "Knapsack DP Memory and Time Profile",
        "Graph BFS/DFS Traversal Scaling Study",
    ]),
    SubjectSpec("discrete", "CS-201", "Discrete Structures Lab", [
        "Propositional Logic Truth-Table Verification",
        "Predicate Logic Counterexample Search",
        "Set Operation Cardinality Experiments",
        "Relation Closure Computation Lab",
    ]),
    SubjectSpec("dld", "CS-220", "Digital Logic Design Lab", [
        "Combinational Circuit Truth-Table Simulation",
        "Karnaugh Map Minimization Verification",
        "Full Adder Delay Propagation Study",
        "Multiplexer Behavioural Simulation Lab",
    ]),
    SubjectSpec("db", "CS-340", "Database Systems Lab", [
        "Indexed vs Full-Scan Query Latency",
        "Join Strategy Cost Comparison",
        "Transaction Isolation Anomaly Lab",
        "Normalization Impact on Query Time",
    ]),
    SubjectSpec("os", "CS-350", "Operating Systems Lab", [
        "CPU Scheduling: FCFS vs SJF vs Round Robin",
        "Page Replacement Hit-Rate Study",
        "Producer-Consumer Synchronization Lab",
        "Disk Scheduling Seek-Time Comparison",
    ]),
    SubjectSpec("networks", "CS-360", "Computer Networks Lab", [
        "Socket Latency and Throughput Trace",
        "TCP vs UDP Packet Loss Experiment",
        "Routing Hop-Count Delay Study",
        "HTTP Request RTT Measurement Lab",
    ]),
    SubjectSpec("se", "CS-370", "Software Engineering Lab", [
        "Unit Test Pass-Rate and Defect Density",
        "Cyclomatic Complexity vs Bug Count",
        "Requirements Traceability Coverage Lab",
        "Code Review Defect Detection Study",
    ]),
    SubjectSpec("web", "CS-380", "Web Technologies Lab", [
        "Page Load Timing Waterfall Analysis",
        "REST API Response Latency Lab",
        "Static vs Dynamic Rendering Cost",
        "CDN Cache Hit-Rate Experiment",
    ]),
    SubjectSpec("ai", "CS-401", "Artificial Intelligence Lab", [
        "Classifier Accuracy and Loss Curves",
        "Confusion Matrix Evaluation Lab",
        "k-NN Distance Metric Comparison",
        "Decision Tree Depth vs Accuracy",
    ]),
    SubjectSpec("security", "CS-410", "Information Security Lab", [
        "Hash Function Throughput Benchmark",
        "Password Strength Entropy Study",
        "AES Encrypt/Decrypt Timing Lab",
        "Brute-Force Attempt Rate Experiment",
    ]),
    SubjectSpec("automata", "CS-301", "Theory of Automata Lab", [
        "DFA Acceptance Trace Verification",
        "NFA to DFA Conversion Cost Study",
        "Regex Match Throughput Lab",
        "Pumping Lemma Counterexample Search",
    ]),
    SubjectSpec("compiler", "CS-420", "Compiler Construction Lab", [
        "Lexer Tokenization Throughput",
        "Parser Error Recovery Rate Lab",
        "AST Node Count Scaling Study",
        "Symbol Table Lookup Benchmark",
    ]),
    SubjectSpec("hci", "CS-430", "Human-Computer Interaction Lab", [
        "Task Completion Time Usability Study",
        "SUS Score Sheet Analysis",
        "Error Rate Across UI Variants",
        "Click-Path Efficiency Experiment",
    ]),
]


def _reg_no(rng: random.Random) -> str:
    return f"{rng.randint(19, 24)}{rng.choice(['I', 'L', 'K', 'F'])}-{rng.randint(1000, 9999)}"


def _student(rng: random.Random) -> tuple[str, str, str, str]:
    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    return name, _reg_no(rng), rng.choice(SECTIONS), rng.choice(INSTRUCTORS)


def _university(rng: random.Random) -> tuple[str, str]:
    uid = rng.choice(list(UNIVERSITY_ALIASES.keys()))
    return uid, rng.choice(UNIVERSITY_ALIASES[uid])


def _date(rng: random.Random) -> str:
    return f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def _fmt(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def _plot_line(xs: list, ys_series: list[tuple[str, list]], xlabel: str, ylabel: str, title: str) -> str:
    out = [
        "import matplotlib.pyplot as plt",
        f"x = {xs!r}",
        "plt.figure(figsize=(6, 4))",
    ]
    for label, ys in ys_series:
        out.append(f"plt.plot(x, {ys!r}, marker='o', label={label!r})")
    out += [
        f"plt.xlabel({xlabel!r})",
        f"plt.ylabel({ylabel!r})",
        f"plt.title({title!r})",
        "plt.legend()",
        "plt.grid(True)",
        "plt.tight_layout()",
        "plt.savefig('plot.png', dpi=300)",
    ]
    return "\n".join(out)


def _cover(rng: random.Random, spec: SubjectSpec, experiment: str) -> dict:
    uid, uraw = _university(rng)
    name, reg, section, instructor = _student(rng)
    return {
        "university_id": uid,
        "university_raw": uraw,
        "department": rng.choice(DEPARTMENTS),
        "course_code": spec.course_code,
        "course_title": spec.course_title,
        "lab_number": f"Lab {rng.randint(1, 12):02d}",
        "experiment_title": experiment,
        "student_name": name,
        "registration_no": reg,
        "section": section,
        "instructor": instructor,
        "submission_date": _date(rng),
    }


def inject_ms_vs_s(
    rows: list[list[str]],
    col: int,
    rng: random.Random,
) -> tuple[list[list[str]], list[str], str, str | None]:
    out = [list(r) for r in rows]
    anomaly_raw: str | None = None
    flags: list[str] = []
    status = "ok"
    if rng.random() < 0.75 and out:
        i = rng.randint(0, len(out) - 1)
        ms_val = float(out[i][col])
        sec_val = ms_val / 1000.0
        key = out[i][0]
        anomaly_raw = f"{key},...,{_fmt(sec_val, 4)}s"
        flags.append(
            f"Entry '{key}' recorded as {_fmt(sec_val, 4)} s while sibling rows use ms "
            f"(1000x unit mismatch detected and normalized to {_fmt(ms_val)} ms)."
        )
        status = "warning"
    return out, flags, status, anomaly_raw


def build_example(rng: random.Random, spec: SubjectSpec) -> dict:
    experiment = rng.choice(spec.experiments)
    cover = _cover(rng, spec, experiment)
    gen = SUBJECT_BUILDERS[spec.key]
    raw_log, report_body, flags, status = gen(rng, experiment)

    report = {
        "cover_page": cover,
        "anomaly_check": {"status": status, "flags": flags},
        "report_body": report_body,
    }
    # Validate strictly
    LabReportSchema.model_validate(report)

    user = (
        f"STUDENT PROFILE:\n"
        f"Name: {cover['student_name']}\n"
        f"Registration No: {cover['registration_no']}\n"
        f"Section: {cover['section']}\n"
        f"University: {cover['university_raw']}\n"
        f"Instructor: {cover['instructor']}\n"
        f"Date: {cover['submission_date']}\n\n"
        f"LAB MANUAL:\n"
        f"Course: {cover['course_code']} — {cover['course_title']}\n"
        f"{cover['lab_number']}: {experiment}\n"
        f"Department: {cover['department']}\n"
        f"Write a grounded lab report from the raw experimental log. "
        f"Audit unit mismatches/outliers. Output JSON only.\n\n"
        f"RAW DATA LOG:\n{raw_log}"
    )
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(report, ensure_ascii=False)},
        ],
        "meta": {"subject": spec.key, "university_id": cover["university_id"]},
    }


def _runtime_style(
    rng: random.Random,
    experiment: str,
    x_label: str,
    xs: list,
    series_names: list[str],
    y_scale: tuple[float, float],
    apparatus: list[str],
    equations: list[str],
    methodology: str,
) -> tuple[str, dict, list[str], str]:
    table_rows: list[list[str]] = []
    series_vals: list[list[float]] = [[] for _ in series_names]
    for x in xs:
        row = [str(x)]
        for si, _name in enumerate(series_names):
            base = rng.uniform(*y_scale) * (1 + hash(str(x)) % 7 * 0.05)
            # scale roughly with x if numeric
            try:
                xf = float(x)
                base *= max(1.0, (xf / float(xs[0])) ** 0.5)
            except (TypeError, ValueError, ZeroDivisionError):
                pass
            val = round(base, 2)
            series_vals[si].append(val)
            row.append(_fmt(val))
        if len(series_names) >= 2:
            speedup = series_vals[0][-1] / max(series_vals[1][-1], 1e-6)
            row.append(_fmt(speedup))
        table_rows.append(row)

    headers = [x_label] + [f"{n} (ms)" for n in series_names]
    if len(series_names) >= 2:
        headers.append("Speedup")

    rows, flags, status, anomaly_raw = inject_ms_vs_s(table_rows, 1, rng)

    log_lines = [f"# experiment={experiment}", ",".join(headers)]
    for r in table_rows:
        log_lines.append(",".join(r))
    if anomaly_raw:
        log_lines.append(f"# RAW_ANOMALY_HINT {anomaly_raw}")
        # also show a corrupted raw line for the model to catch
        bad = list(table_rows[0])
        ms = float(bad[1])
        bad[1] = f"{ms/1000:.4f}s"
        log_lines.append("# corrupted_observation," + ",".join(bad))

    plot = _plot_line(
        [float(x) if str(x).replace(".", "", 1).isdigit() else i for i, x in enumerate(xs)],
        [(series_names[i], series_vals[i]) for i in range(len(series_names))],
        x_label,
        "Runtime (ms)",
        experiment[:60],
    )

    primary = series_names[0]
    last = series_vals[0][-1]
    body = {
        "abstract": (
            f"This lab investigated {experiment.lower()}. Measurements were collected for "
            f"{x_label} across {len(xs)} configurations using a controlled timing harness. "
            f"The primary metric was wall-clock runtime in milliseconds for {primary}. "
            f"At the largest setting, {primary} averaged {_fmt(last)} ms."
        ),
        "apparatus": apparatus,
        "methodology": methodology,
        "equations_latex": equations,
        "tables": [{"caption": f"{experiment} — measured results", "headers": headers, "rows": rows}],
        "plot_code": plot,
        "discussion": (
            f"Results show how {primary} scales with {x_label}. "
            + (
                "A unit mismatch was present in the raw log and normalized to milliseconds before analysis. "
                if flags
                else "No unit anomalies were detected in the raw log. "
            )
            + "Trends align with expected algorithmic or system behaviour for this exercise. "
            "Variance across trials was low enough for comparative conclusions."
        ),
        "conclusion": (
            f"The experiment confirmed expected behaviour for {experiment}. "
            "All tabulated values are grounded in the uploaded raw log after anomaly normalization."
        ),
    }
    return "\n".join(log_lines), body, flags, status


def gen_pf(rng, experiment):
    xs = [1000, 10000, 100000, 1000000]
    return _runtime_style(
        rng, experiment, "N", xs, ["LoopA", "LoopB"], (0.2, 2.0),
        ["Python 3.11", "time.perf_counter harness", "CSV runtime log"],
        [r"T(N)=\sum_{i=1}^{N} t_i", r"\text{Speedup}=T_A/T_B"],
        "Implemented both loop variants, executed each size three times, and logged mean runtime to CSV.",
    )


def gen_oop(rng, experiment):
    xs = [10, 50, 100, 200]
    rows = []
    cov, pass_rate = [], []
    for c in xs:
        coverage = round(rng.uniform(62, 98), 1)
        passed = round(rng.uniform(70, 100), 1)
        cov.append(coverage)
        pass_rate.append(passed)
        rows.append([str(c), _fmt(coverage, 1), _fmt(passed, 1), str(rng.randint(0, 8))])
    headers = ["NumClasses", "Coverage (%)", "PassRate (%)", "Defects"]
    flags, status = [], "ok"
    if rng.random() < 0.7:
        # outlier defect spike
        i = rng.randint(0, len(rows) - 1)
        rows[i][3] = str(int(rows[i][3]) + rng.randint(25, 40))
        flags.append(
            f"Defect count for NumClasses={rows[i][0]} is an extreme outlier "
            f"({rows[i][3]}) relative to peer configurations; flagged for review."
        )
        status = "warning"
    log = ["# oop_unit_tests"] + [",".join(headers)] + [",".join(r) for r in rows]
    body = {
        "abstract": (
            f"This OOP lab evaluated {experiment.lower()}. Test coverage and pass rates were "
            f"recorded for hierarchies of different sizes. Maximum coverage observed was {_fmt(max(cov), 1)}%."
        ),
        "apparatus": ["JUnit / pytest", "Coverage.py or JaCoCo", "CSV test summary"],
        "methodology": "Built class hierarchies, executed the unit suite, and exported coverage and pass-rate metrics.",
        "equations_latex": [r"\text{Coverage}=\frac{\text{lines hit}}{\text{lines total}}\times 100"],
        "tables": [{"caption": "OOP test metrics", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(xs, [("Coverage", cov), ("PassRate", pass_rate)], "NumClasses", "Percent", experiment[:60]),
        "discussion": (
            "Coverage generally improved with more focused tests. "
            + ("An outlier defect spike was flagged from the raw log. " if flags else "")
            + "Pass rate remained acceptable for the lab rubric."
        ),
        "conclusion": "OOP lab objectives were met; metrics are grounded in the test CSV.",
    }
    return "\n".join(log), body, flags, status


def gen_ds(rng, experiment):
    xs = [1000, 5000, 20000, 100000]
    return _runtime_style(
        rng, experiment, "N", xs, ["StructA", "StructB"], (0.15, 3.5),
        ["C++17 / Java 17", "microbenchmark harness", "operation CSV log"],
        [r"T_{\text{op}}(N)=\frac{1}{k}\sum t_i", r"O(f(N))\ \text{empirical fit}"],
        "Executed insert/lookup workloads for each structure and logged mean operation time.",
    )


def gen_algo(rng, experiment):
    xs = [1000, 10000, 100000, 1000000]
    return _runtime_style(
        rng, experiment, "N", xs, ["AlgoA", "AlgoB"], (0.3, 4.0),
        ["GCC 13 / Clang", "Python 3.11 timing harness", "CSV runtime log"],
        [r"T_{\text{avg}}(N)=\frac{1}{k}\sum_{i=1}^{k} t_i(N)", r"\text{Speedup}=T_A/T_B"],
        "Generated random inputs per size, ran each algorithm for fixed trials, and stored mean milliseconds.",
    )


def gen_discrete(rng, experiment):
    headers = ["Formula", "Cases", "True", "False", "Verified"]
    formulas = ["P→Q", "P∧Q", "¬(P∨Q)", "P↔Q", "(P→Q)∧(Q→R)"]
    rows = []
    for f in formulas:
        cases = 4 if "R" not in f else 8
        true_n = rng.randint(1, cases - 1)
        rows.append([f, str(cases), str(true_n), str(cases - true_n), rng.choice(["yes", "yes", "no"])])
    flags, status = [], "ok"
    if rng.random() < 0.65:
        i = rng.randint(0, len(rows) - 1)
        # inconsistent True+False vs Cases
        rows[i][2] = str(int(rows[i][1]) + 2)
        flags.append(
            f"Truth-table counts for '{rows[i][0]}' are inconsistent: True+False exceeds Cases; flagged anomaly."
        )
        status = "warning"
    log = ["# discrete_truth_tables", ",".join(headers)] + [",".join(r) for r in rows]
    xs = list(range(len(formulas)))
    true_counts = [int(r[2]) for r in rows]
    body = {
        "abstract": (
            f"This discrete structures lab performed {experiment.lower()}. "
            f"{len(formulas)} propositional forms were evaluated via exhaustive truth tables."
        ),
        "apparatus": ["Logic toolkit / Python truth-table script", "CSV case log"],
        "methodology": "Enumerated assignments for each formula, counted satisfying cases, and verified identities.",
        "equations_latex": [r"P\to Q \equiv \neg P \lor Q", r"|\{v: v\models \phi\}|"],
        "tables": [{"caption": "Truth-table verification", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(xs, [("TrueCount", true_counts)], "FormulaIndex", "True assignments", experiment[:60]),
        "discussion": (
            "Most identities verified as expected. "
            + ("An inconsistent count row was flagged from the raw log. " if flags else "")
            + "Manual spot checks matched the generator output."
        ),
        "conclusion": "Discrete lab outcomes are consistent with theory after anomaly review.",
    }
    return "\n".join(log), body, flags, status


def gen_dld(rng, experiment):
    headers = ["A", "B", "Cin", "Sum", "Cout", "Delay_ns"]
    rows = []
    delays = []
    for a in (0, 1):
        for b in (0, 1):
            for cin in (0, 1):
                total = a + b + cin
                delay = round(rng.uniform(0.8, 2.4), 2)
                delays.append(delay)
                rows.append([str(a), str(b), str(cin), str(total % 2), str(total // 2), _fmt(delay)])
    flags, status = [], "ok"
    if rng.random() < 0.7:
        i = rng.randint(0, len(rows) - 1)
        # wrong sum bit
        rows[i][3] = str(1 - int(rows[i][3]))
        flags.append(
            f"Truth-table Sum bit anomaly at A={rows[i][0]},B={rows[i][1]},Cin={rows[i][2]} "
            f"(inconsistent with A+B+Cin); flagged."
        )
        status = "warning"
    log = ["# dld_sim"] + [",".join(headers)] + [",".join(r) for r in rows]
    body = {
        "abstract": (
            f"This digital logic lab simulated {experiment.lower()}. "
            f"All 8 input combinations were evaluated with delay annotations in nanoseconds."
        ),
        "apparatus": ["Logic simulator / Logisim-style tool", "truth-table CSV export"],
        "methodology": "Swept inputs A,B,Cin, recorded Sum/Cout, and logged gate delay estimates.",
        "equations_latex": [r"Sum=A\oplus B\oplus C_{in}", r"C_{out}=majority(A,B,C_{in})"],
        "tables": [{"caption": "Full-adder style simulation", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(list(range(len(delays))), [("Delay_ns", delays)], "VectorIndex", "Delay (ns)", experiment[:60]),
        "discussion": (
            "Logic outputs mostly matched Boolean expectations. "
            + ("At least one inconsistent Sum entry was flagged. " if flags else "")
            + "Delay stayed within typical educational-sim bounds."
        ),
        "conclusion": "DLD simulation objectives were achieved with grounded table values.",
    }
    return "\n".join(log), body, flags, status


def gen_db(rng, experiment):
    xs = [1000, 10000, 100000, 1000000]
    return _runtime_style(
        rng, experiment, "Rows", xs, ["FullScan", "Indexed"], (1.0, 8.0),
        ["PostgreSQL / SQLite", "EXPLAIN ANALYZE", "query timing CSV"],
        [r"T_{scan}\propto N", r"T_{index}\propto \log N"],
        "Loaded synthetic tables, ran identical queries with and without indexes, and logged latency.",
    )


def gen_os(rng, experiment):
    headers = ["Algorithm", "AvgWaiting (ms)", "AvgTurnaround (ms)", "ContextSwitches"]
    algos = ["FCFS", "SJF", "RoundRobin", "Priority"]
    rows = []
    wait_vals = []
    for a in algos:
        w = round(rng.uniform(20, 180), 1)
        t = round(w + rng.uniform(30, 120), 1)
        wait_vals.append(w)
        rows.append([a, _fmt(w, 1), _fmt(t, 1), str(rng.randint(5, 40))])
    rows, flags, status, anomaly_raw = inject_ms_vs_s(rows, 1, rng)
    log = ["# os_scheduling", ",".join(headers)] + [",".join(r) for r in rows]
    if anomaly_raw:
        log.append(f"# RAW_ANOMALY_HINT {anomaly_raw}")
    body = {
        "abstract": (
            f"This OS lab compared CPU scheduling via {experiment.lower()}. "
            f"Average waiting and turnaround times were collected for {len(algos)} policies."
        ),
        "apparatus": ["Scheduling simulator", "process burst CSV", "Python analysis script"],
        "methodology": "Fed identical process burst sets to each scheduler and recorded waiting/turnaround metrics.",
        "equations_latex": [
            r"W_{avg}=\frac{1}{n}\sum W_i",
            r"T_{avg}=\frac{1}{n}\sum (C_i-A_i)",
        ],
        "tables": [{"caption": "Scheduler comparison", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(list(range(len(algos))), [("AvgWaiting", wait_vals)], "AlgorithmIndex", "Waiting (ms)", experiment[:60]),
        "discussion": (
            "SJF typically reduced waiting time versus FCFS in these traces. "
            + ("A millisecond/second unit mismatch was normalized. " if flags else "")
            + "Round Robin context-switch overhead was visible in the counters."
        ),
        "conclusion": "Scheduling results match expected OS theory for the provided workload.",
    }
    return "\n".join(log), body, flags, status


def gen_networks(rng, experiment):
    xs = [64, 256, 512, 1024, 1500]
    return _runtime_style(
        rng, experiment, "PayloadB", xs, ["TCP", "UDP"], (0.5, 6.0),
        ["Wireshark / tcpdump export", "iperf-style generator", "latency CSV"],
        [r"Throughput=\frac{\text{bytes}\times 8}{\text{time}}", r"RTT=T_{ack}-T_{send}"],
        "Sent fixed-size payloads across the lab network and logged RTT/throughput samples.",
    )


def gen_se(rng, experiment):
    headers = ["Module", "LOC", "Tests", "Passed", "Defects", "PassRate (%)"]
    modules = ["Auth", "Billing", "Search", "Notify", "Admin"]
    rows, rates = [], []
    for m in modules:
        tests = rng.randint(20, 80)
        passed = rng.randint(int(tests * 0.7), tests)
        rate = round(100.0 * passed / tests, 1)
        rates.append(rate)
        rows.append([m, str(rng.randint(200, 2000)), str(tests), str(passed), str(rng.randint(0, 12)), _fmt(rate, 1)])
    flags, status = [], "ok"
    if rng.random() < 0.7:
        i = rng.randint(0, len(rows) - 1)
        rows[i][3] = str(int(rows[i][2]) + 5)  # passed > tests
        flags.append(
            f"Module '{rows[i][0]}' reports Passed > Tests ({rows[i][3]} > {rows[i][2]}); data anomaly flagged."
        )
        status = "warning"
    log = ["# se_quality"] + [",".join(headers)] + [",".join(r) for r in rows]
    body = {
        "abstract": (
            f"This software engineering lab analyzed {experiment.lower()}. "
            f"Five modules were assessed for test pass rate and defect counts."
        ),
        "apparatus": ["CI test report", "static metrics CSV", "issue tracker export"],
        "methodology": "Collected per-module LOC, test totals, passes, and logged defects from the tracker.",
        "equations_latex": [r"\text{PassRate}=\frac{\text{Passed}}{\text{Tests}}\times 100", r"\text{DefectDensity}=\frac{\text{Defects}}{KLOC}"],
        "tables": [{"caption": "SE quality metrics", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(list(range(len(modules))), [("PassRate", rates)], "ModuleIndex", "PassRate (%)", experiment[:60]),
        "discussion": (
            "Pass rates were generally high. "
            + ("An impossible Passed>Tests row was flagged. " if flags else "")
            + "Defect density correlated loosely with module size."
        ),
        "conclusion": "SE lab metrics support the project quality discussion and are log-grounded.",
    }
    return "\n".join(log), body, flags, status


def gen_web(rng, experiment):
    xs = [1, 2, 3, 4, 5]
    return _runtime_style(
        rng, experiment, "PageID", xs, ["TTFB", "FullLoad"], (40, 400),
        ["Chrome DevTools HAR", "Lighthouse CSV", "local Node server"],
        [r"TTFB=T_{firstByte}-T_{request}", r"FullLoad=T_{loadEvent}-T_{request}"],
        "Captured HAR timings for each page variant and exported millisecond measurements.",
    )


def gen_ai(rng, experiment):
    headers = ["Epoch", "Loss", "Accuracy (%)", "ValAccuracy (%)"]
    rows, acc = [], []
    loss = rng.uniform(1.2, 2.0)
    a = rng.uniform(40, 55)
    for e in range(1, 6):
        loss = max(0.15, loss * rng.uniform(0.75, 0.92))
        a = min(97.0, a + rng.uniform(3, 8))
        va = min(96.0, a - rng.uniform(0, 4))
        acc.append(round(a, 2))
        rows.append([str(e), _fmt(loss), _fmt(a), _fmt(va)])
    flags, status = [], "ok"
    if rng.random() < 0.65:
        i = rng.randint(1, len(rows) - 1)
        rows[i][2] = _fmt(float(rows[i - 1][2]) - rng.uniform(15, 25))
        flags.append(
            f"Accuracy dropped sharply at epoch {rows[i][0]} ({rows[i][2]}%); outlier flagged for review."
        )
        status = "warning"
    log = ["# ai_metrics"] + [",".join(headers)] + [",".join(r) for r in rows]
    body = {
        "abstract": (
            f"This AI lab tracked {experiment.lower()}. "
            f"Training ran for 5 epochs with loss and accuracy exported each epoch."
        ),
        "apparatus": ["Python / scikit-learn or PyTorch", "metrics CSV", "fixed random seed"],
        "methodology": "Trained the model for five epochs on the lab split and logged loss/accuracy each epoch.",
        "equations_latex": [r"Accuracy=\frac{TP+TN}{TP+TN+FP+FN}", r"\mathcal{L}=-\sum y\log\hat{y}"],
        "tables": [{"caption": "Training metrics", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(list(range(1, 6)), [("Accuracy", acc)], "Epoch", "Accuracy (%)", experiment[:60]),
        "discussion": (
            "Accuracy trended upward as loss decreased. "
            + ("A sharp accuracy drop was flagged as an anomaly. " if flags else "")
            + "Validation tracked training within a small gap."
        ),
        "conclusion": "AI lab metrics demonstrate learning dynamics grounded in the log.",
    }
    return "\n".join(log), body, flags, status


def gen_security(rng, experiment):
    xs = [1000, 10000, 100000, 1000000]
    return _runtime_style(
        rng, experiment, "Ops", xs, ["SHA256", "AES"], (0.2, 5.0),
        ["OpenSSL / hashlib", "microbenchmark harness", "timing CSV"],
        [r"Throughput=\frac{\text{ops}}{\text{seconds}}", r"H(m)=\mathrm{SHA256}(m)"],
        "Repeated hash/encrypt operations for each batch size and logged mean latency.",
    )


def gen_automata(rng, experiment):
    headers = ["String", "Expected", "DFA", "NFA", "Match"]
    strings = ["ab", "aab", "bab", "aaaa", "ε", "abba", "baab"]
    rows = []
    for s in strings:
        exp = rng.choice(["accept", "reject"])
        dfa = exp if rng.random() > 0.15 else ("reject" if exp == "accept" else "accept")
        nfa = exp
        match = "yes" if dfa == exp else "no"
        rows.append([s, exp, dfa, nfa, match])
    flags = [f"DFA mismatch on '{r[0]}' (expected {r[1]}, got {r[2]})" for r in rows if r[4] == "no"]
    status = "warning" if flags else "ok"
    if flags:
        flags = flags[:2]
        flags[0] = flags[0] + "; flagged as acceptance anomaly."
    log = ["# automata_trace"] + [",".join(headers)] + [",".join(r) for r in rows]
    xs = list(range(len(strings)))
    match_score = [1 if r[4] == "yes" else 0 for r in rows]
    body = {
        "abstract": (
            f"This automata lab verified {experiment.lower()}. "
            f"{len(strings)} strings were tested on DFA/NFA implementations against expected labels."
        ),
        "apparatus": ["Automata simulator", "test-string CSV", "Python driver"],
        "methodology": "Loaded the target language machines, ran each string, and compared outputs to the oracle.",
        "equations_latex": [r"L(M)=\{w\mid \hat{\delta}(q_0,w)\in F\}"],
        "tables": [{"caption": "Acceptance traces", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(xs, [("Correct", match_score)], "StringIndex", "Match (0/1)", experiment[:60]),
        "discussion": (
            "NFA results were stable. "
            + ("One or more DFA mismatches were flagged from the trace. " if flags else "")
            + "Discrepancies were traced to transition-table typos in the student log."
        ),
        "conclusion": "Automata acceptance behaviour was audited against the raw trace log.",
    }
    return "\n".join(log), body, flags, status


def gen_compiler(rng, experiment):
    xs = [100, 500, 2000, 8000]
    return _runtime_style(
        rng, experiment, "LOC", xs, ["Lexer", "Parser"], (0.4, 7.0),
        ["Flex/Bison or ANTLR", "token dump", "timing CSV"],
        [r"T_{lex}\propto N", r"Tokens\approx c\cdot LOC"],
        "Fed source fixtures of increasing size through lexer/parser and logged stage timings.",
    )


def gen_hci(rng, experiment):
    headers = ["Participant", "TaskTime (s)", "Errors", "SUS"]
    rows, times = [], []
    for p in range(1, 9):
        t = round(rng.uniform(12, 95), 1)
        times.append(t)
        rows.append([f"P{p}", _fmt(t, 1), str(rng.randint(0, 5)), str(rng.randint(55, 95))])
    flags, status = [], "ok"
    if rng.random() < 0.7:
        i = rng.randint(0, len(rows) - 1)
        rows[i][1] = _fmt(float(rows[i][1]) * 8, 1)
        flags.append(
            f"Participant {rows[i][0]} task time {_fmt(float(rows[i][1]), 1)} s is an extreme outlier; flagged."
        )
        status = "warning"
    log = ["# hci_usability"] + [",".join(headers)] + [",".join(r) for r in rows]
    # convert plot times from cleaned perspective (still use listed times for series)
    body = {
        "abstract": (
            f"This HCI lab conducted {experiment.lower()}. "
            f"Eight participants completed the primary task with SUS scores recorded."
        ),
        "apparatus": ["Prototype UI", "stopwatch / event logger", "SUS questionnaire CSV"],
        "methodology": "Participants performed the scripted task once; time, errors, and SUS were logged.",
        "equations_latex": [r"SUS=2.5\times\sum \text{adjusted item scores}"],
        "tables": [{"caption": "Usability session log", "headers": headers, "rows": rows}],
        "plot_code": _plot_line(list(range(1, 9)), [("TaskTime", [float(r[1]) for r in rows])], "Participant", "Task time (s)", experiment[:60]),
        "discussion": (
            "Most participants completed the task within a similar band. "
            + ("An extreme task-time outlier was flagged. " if flags else "")
            + "SUS scores indicate acceptable perceived usability for a lab prototype."
        ),
        "conclusion": "HCI findings are grounded in the session CSV and support the design iteration notes.",
    }
    return "\n".join(log), body, flags, status


SUBJECT_BUILDERS = {
    "pf": gen_pf,
    "oop": gen_oop,
    "ds": gen_ds,
    "algo": gen_algo,
    "discrete": gen_discrete,
    "dld": gen_dld,
    "db": gen_db,
    "os": gen_os,
    "networks": gen_networks,
    "se": gen_se,
    "web": gen_web,
    "ai": gen_ai,
    "security": gen_security,
    "automata": gen_automata,
    "compiler": gen_compiler,
    "hci": gen_hci,
}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            # training format: messages only
            f.write(json.dumps({"messages": row["messages"]}, ensure_ascii=False) + "\n")


def main() -> None:
    assert UNIVERSITIES_PATH.exists(), f"missing {UNIVERSITIES_PATH}"
    registry = json.loads(UNIVERSITIES_PATH.read_text(encoding="utf-8"))
    for uid in UNIVERSITY_ALIASES:
        assert uid in registry, f"alias uid {uid} not in universities.json"

    rng = random.Random(SEED)
    examples: list[dict] = []
    for spec in SUBJECTS:
        for i in range(SAMPLES_PER_SUBJECT):
            # deterministic but varied per subject index
            local = random.Random(SEED + hash((spec.key, i)) % 10_000_000)
            examples.append(build_example(local, spec))

    rng.shuffle(examples)
    assert len(examples) == SAMPLES_PER_SUBJECT * len(SUBJECTS)

    train = examples[:TRAIN_N]
    valid = examples[TRAIN_N : TRAIN_N + VALID_N]
    test = examples[TRAIN_N + VALID_N :]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATA_DIR / "train.jsonl", train)
    write_jsonl(DATA_DIR / "valid.jsonl", valid)
    write_jsonl(DATA_DIR / "test.jsonl", test)

    # subject coverage summary
    from collections import Counter

    def counts(rows: list[dict]) -> dict[str, int]:
        return dict(Counter(r["meta"]["subject"] for r in rows))

    summary = {
        "total": len(examples),
        "train": len(train),
        "valid": len(valid),
        "test": len(test),
        "subjects": len(SUBJECTS),
        "samples_per_subject": SAMPLES_PER_SUBJECT,
        "train_subject_counts": counts(train),
        "test_subject_counts": counts(test),
    }
    (DATA_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {DATA_DIR / 'train.jsonl'}")
    print(f"wrote {DATA_DIR / 'valid.jsonl'}")
    print(f"wrote {DATA_DIR / 'test.jsonl'}")


if __name__ == "__main__":
    main()
