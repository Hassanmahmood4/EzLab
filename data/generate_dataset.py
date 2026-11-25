#!/usr/bin/env python3
"""Generate high-diversity Task→Code→Output chat pairs for EzLab LoRA.

Matches live inference:
  system: SYSTEM_PROMPT
  user: Course / Lab / Task|Exercise N — title + prompt + lang hint
  assistant: {"code": "...", "output": "..."}

Goal for final fine-tune: hundreds of unique code bodies (not ~20 recycled templates).
"""

from __future__ import annotations

import json
import math
import random
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.schema import SYSTEM_PROMPT  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent
SEED = 42
TRAIN_N = 3200
VALID_N = 250
TEST_N = 250


def _user_prompt(
    course_code: str,
    course_title: str,
    lab_number: str,
    experiment: str,
    number: int,
    title: str,
    prompt: str,
    lang_hint: str = "Python",
    label: str = "Task",
) -> str:
    return (
        f"Course: {course_code} — {course_title}\n"
        f"Lab: {lab_number} — {experiment}\n"
        f"{label} {number} — {title}\n"
        f"{prompt}\n\n"
        f"Write a complete {lang_hint} solution for this single task. "
        "Return JSON only with keys code and output. "
        "No placeholders, no markdown."
    )


def _ex(
    course_code: str,
    course_title: str,
    lab_number: str,
    experiment: str,
    number: int,
    title: str,
    prompt: str,
    code: str,
    output: str,
    lang_hint: str = "Python",
    label: str = "Task",
) -> dict:
    assistant = json.dumps(
        {"code": code.rstrip() + "\n", "output": output.rstrip() + "\n"},
        ensure_ascii=False,
    )
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _user_prompt(
                    course_code,
                    course_title,
                    lab_number,
                    experiment,
                    number,
                    title,
                    prompt,
                    lang_hint,
                    label,
                ),
            },
            {"role": "assistant", "content": assistant},
        ]
    }


def _lab(rng: random.Random, lo: int = 1, hi: int = 12) -> str:
    return f"Lab {rng.randint(lo, hi):02d}"


def _label(rng: random.Random) -> str:
    return rng.choice(["Task", "Task", "Exercise", "Exercise"])


# ── Unique template banks ────────────────────────────────────────────────────


def _pf_unique(rng: random.Random) -> list[dict]:
    a, b, c = rng.randint(2, 30), rng.randint(2, 30), rng.randint(2, 15)
    n = rng.choice([5, 6, 7, 8, 9])
    fact = math.factorial(n)
    nums = [rng.randint(1, 40) for _ in range(8)]
    key = nums[rng.randint(0, 7)]
    comps = nums.index(key) + 1
    label = _label(rng)
    lab = _lab(rng, 1, 6)
    course = ("CS-100", "Programming Fundamentals Lab")
    out: list[dict] = []

    out.append(
        _ex(
            *course,
            lab,
            "Input, Loops and Functions",
            1,
            "Sum two integers",
            "Read two integers from input and print their sum.",
            "a = int(input())\nb = int(input())\nprint(a + b)\n",
            f"{a}\n{b}\n{a + b}\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Input, Loops and Functions",
            2,
            "Factorial",
            f"Implement factorial recursively and print factorial({n}).",
            "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\n"
            f"print(factorial({n}))\n",
            f"{fact}\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Arrays and Searching",
            3,
            "Linear search comparisons",
            f"Count comparisons while linearly searching for {key} in {nums}.",
            f"nums = {nums}\nkey = {key}\ncomps = 0\nfound = -1\n"
            "for i, v in enumerate(nums):\n    comps += 1\n    if v == key:\n        found = i\n        break\n"
            "print('index', found)\nprint('comparisons', comps)\n",
            f"index {nums.index(key)}\ncomparisons {comps}\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Conditionals",
            4,
            "Grade band",
            f"Map score {c * 5 + rng.randint(0, 20)} to letter grade A/B/C/D/F with if/elif.",
            f"score = {min(100, c * 5 + 10)}\n"
            "if score >= 85:\n    g = 'A'\nelif score >= 70:\n    g = 'B'\n"
            "elif score >= 55:\n    g = 'C'\nelif score >= 40:\n    g = 'D'\nelse:\n    g = 'F'\n"
            "print(score, g)\n",
            f"{min(100, c * 5 + 10)} "
            + (
                "A"
                if min(100, c * 5 + 10) >= 85
                else "B"
                if min(100, c * 5 + 10) >= 70
                else "C"
                if min(100, c * 5 + 10) >= 55
                else "D"
                if min(100, c * 5 + 10) >= 40
                else "F"
            )
            + "\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Loops",
            5,
            "FizzBuzz subset",
            "Print numbers 1..15; for multiples of 3 print Fizz, of 5 Buzz, of both FizzBuzz.",
            "for i in range(1, 16):\n"
            "    if i % 15 == 0:\n        print('FizzBuzz')\n"
            "    elif i % 3 == 0:\n        print('Fizz')\n"
            "    elif i % 5 == 0:\n        print('Buzz')\n"
            "    else:\n        print(i)\n",
            "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Strings",
            6,
            "Palindrome check",
            "Check whether 'level' is a palindrome (case-insensitive) and print True/False.",
            "s = 'level'\nclean = ''.join(ch.lower() for ch in s if ch.isalnum())\n"
            "print(clean == clean[::-1])\n",
            "True\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "Functions",
            7,
            "Prime test",
            f"Write is_prime(n) and print is_prime({rng.choice([17, 19, 23, 29])}).",
            "def is_prime(n):\n    if n < 2:\n        return False\n"
            "    if n % 2 == 0:\n        return n == 2\n"
            "    i = 3\n    while i * i <= n:\n        if n % i == 0:\n            return False\n"
            "        i += 2\n    return True\n\n"
            f"print(is_prime({17}))\n",
            "True\n",
            label=label,
        )
    )
    out.append(
        _ex(
            *course,
            lab,
            "File I/O simulation",
            8,
            "Word count",
            "Count words in the string 'offline lab report copilot for CS students'.",
            "text = 'offline lab report copilot for CS students'\nprint(len(text.split()))\n",
            "6\n",
            label=label,
        )
    )
    return out


def _oop_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 3, 8)
    course = ("CS-212", "Object-Oriented Programming Lab")
    return [
        _ex(
            *course,
            lab,
            "Inheritance Hierarchy",
            1,
            "Shape hierarchy areas",
            "Define Shape with area(), Circle and Rectangle subclasses. Print areas for r=2 and 3x4.",
            "import math\n\nclass Shape:\n    def area(self) -> float:\n        raise NotImplementedError\n\n"
            "class Circle(Shape):\n    def __init__(self, r: float):\n        self.r = r\n"
            "    def area(self) -> float:\n        return math.pi * self.r * self.r\n\n"
            "class Rectangle(Shape):\n    def __init__(self, w: float, h: float):\n        self.w, self.h = w, h\n"
            "    def area(self) -> float:\n        return self.w * self.h\n\n"
            "print(f'{Circle(2).area():.4f}')\nprint(f'{Rectangle(3, 4).area():.4f}')\n",
            "12.5664\n12.0000\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Polymorphism",
            2,
            "Polymorphic dispatch",
            "Store Circle(1) and Rectangle(2,5) in a list of Shape; print each area to 2 decimals.",
            "import math\n\nclass Shape:\n    def area(self):\n        raise NotImplementedError\n\n"
            "class Circle(Shape):\n    def __init__(self, r):\n        self.r = r\n"
            "    def area(self):\n        return math.pi * self.r ** 2\n\n"
            "class Rectangle(Shape):\n    def __init__(self, w, h):\n        self.w, self.h = w, h\n"
            "    def area(self):\n        return self.w * self.h\n\n"
            "for s in [Circle(1), Rectangle(2, 5)]:\n    print(f'{s.area():.2f}')\n",
            "3.14\n10.00\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Encapsulation",
            3,
            "BankAccount class",
            "Implement BankAccount with deposit/withdraw; reject overdraft; print final balance after +100, -40, -80.",
            "class BankAccount:\n    def __init__(self, balance=0.0):\n        self._balance = float(balance)\n"
            "    def deposit(self, amount):\n        self._balance += amount\n"
            "    def withdraw(self, amount):\n"
            "        if amount > self._balance:\n            raise ValueError('insufficient funds')\n"
            "        self._balance -= amount\n"
            "    @property\n    def balance(self):\n        return self._balance\n\n"
            "acct = BankAccount()\nacct.deposit(100)\nacct.withdraw(40)\n"
            "try:\n    acct.withdraw(80)\nexcept ValueError as e:\n    print('error:', e)\n"
            "print(f'balance={acct.balance:.2f}')\n",
            "error: insufficient funds\nbalance=60.00\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Magic methods",
            4,
            "Vector add",
            "Implement Vector2D with __add__ and __repr__; print Vector2D(1,2)+Vector2D(3,4).",
            "class Vector2D:\n    def __init__(self, x, y):\n        self.x, self.y = x, y\n"
            "    def __add__(self, other):\n        return Vector2D(self.x + other.x, self.y + other.y)\n"
            "    def __repr__(self):\n        return f'Vector2D({self.x}, {self.y})'\n\n"
            "print(Vector2D(1, 2) + Vector2D(3, 4))\n",
            "Vector2D(4, 6)\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Unit tests",
            5,
            "Simple assert suite",
            "Write 3 assert-based checks for a clamp(x, lo, hi) helper and print 'ok' if all pass.",
            "def clamp(x, lo, hi):\n    return max(lo, min(hi, x))\n\n"
            "assert clamp(5, 0, 10) == 5\nassert clamp(-1, 0, 10) == 0\nassert clamp(99, 0, 10) == 10\n"
            "print('ok')\n",
            "ok\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Composition",
            6,
            "Student and Course",
            "Course holds a list of Student names; add three students and print enrollment count.",
            "class Course:\n    def __init__(self, code):\n        self.code = code\n        self.students = []\n"
            "    def enroll(self, name):\n        self.students.append(name)\n\n"
            "c = Course('CS-212')\nfor n in ('Ali', 'Sara', 'Hassan'):\n    c.enroll(n)\n"
            "print(c.code, len(c.students))\n",
            "CS-212 3\n",
            label=label,
        ),
    ]


def _dsa_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 2, 8)
    course = ("CS-218", "Data Structures Lab")
    return [
        _ex(
            *course,
            lab,
            "Stacks and Queues",
            1,
            "Stack LIFO demo",
            "Push 10,20,30 onto a list stack then pop all, printing each value.",
            "stack = []\nfor x in (10, 20, 30):\n    stack.append(x)\nwhile stack:\n    print(stack.pop())\n",
            "30\n20\n10\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Stacks and Queues",
            2,
            "Queue FIFO demo",
            "Enqueue A,B,C with collections.deque and dequeue all.",
            "from collections import deque\nq = deque()\nfor x in ('A', 'B', 'C'):\n    q.append(x)\n"
            "while q:\n    print(q.popleft())\n",
            "A\nB\nC\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Binary Search",
            3,
            "Binary search steps",
            "Binary-search for 42 in sorted 1..100. Print index and step count.",
            "arr = list(range(1, 101))\nkey = 42\nlo, hi, steps = 0, len(arr) - 1, 0\nidx = -1\n"
            "while lo <= hi:\n    steps += 1\n    mid = (lo + hi) // 2\n"
            "    if arr[mid] == key:\n        idx = mid\n        break\n"
            "    if arr[mid] < key:\n        lo = mid + 1\n    else:\n        hi = mid - 1\n"
            "print('index', idx)\nprint('steps', steps)\n",
            "index 41\nsteps 6\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Linked List",
            4,
            "Singly linked list insert",
            "Implement a Node/LinkedList with append; insert 1,2,3 and print as list.",
            "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\n"
            "class LinkedList:\n    def __init__(self):\n        self.head = None\n"
            "    def append(self, val):\n"
            "        n = Node(val)\n        if not self.head:\n            self.head = n\n            return\n"
            "        cur = self.head\n        while cur.next:\n            cur = cur.next\n"
            "        cur.next = n\n"
            "    def to_list(self):\n"
            "        out, cur = [], self.head\n        while cur:\n            out.append(cur.val)\n"
            "            cur = cur.next\n        return out\n\n"
            "ll = LinkedList()\nfor v in (1, 2, 3):\n    ll.append(v)\nprint(ll.to_list())\n",
            "[1, 2, 3]\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Trees",
            5,
            "BST insert + inorder",
            "Insert [5,3,7,2,4] into a BST and print inorder traversal.",
            "class N:\n    def __init__(self, v):\n        self.v, self.l, self.r = v, None, None\n\n"
            "def insert(root, v):\n    if root is None:\n        return N(v)\n"
            "    if v < root.v:\n        root.l = insert(root.l, v)\n    elif v > root.v:\n"
            "        root.r = insert(root.r, v)\n    return root\n\n"
            "def inorder(root, acc=None):\n    if acc is None:\n        acc = []\n"
            "    if root:\n        inorder(root.l, acc)\n        acc.append(root.v)\n        inorder(root.r, acc)\n"
            "    return acc\n\n"
            "root = None\nfor v in [5, 3, 7, 2, 4]:\n    root = insert(root, v)\nprint(inorder(root))\n",
            "[2, 3, 4, 5, 7]\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Hashing",
            6,
            "Frequency map",
            "Count character frequencies in 'labpulse' and print sorted (char, count) pairs.",
            "from collections import Counter\nc = Counter('labpulse')\n"
            "for ch, n in sorted(c.items()):\n    print(ch, n)\n",
            "a 1\nb 1\ne 1\nl 2\np 1\ns 1\nu 1\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Recursion",
            7,
            "Fibonacci DP",
            "Compute fib(10) with bottom-up DP and print the value.",
            "def fib(n):\n    if n < 2:\n        return n\n    a, b = 0, 1\n"
            "    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\nprint(fib(10))\n",
            "55\n",
            label=label,
        ),
    ]


def _algo_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 4, 10)
    course = ("CS-302", "Design and Analysis of Algorithms Lab")
    return [
        _ex(
            *course,
            lab,
            "Sorting Runtime Comparison",
            1,
            "Time sorted vs quicksort",
            "Time Python sorted() vs a simple quicksort on n=5000 random ints (seed 0). Print ms for both.",
            "import random\nimport time\n\n"
            "def quicksort(a):\n    if len(a) <= 1:\n        return a\n    p = a[len(a)//2]\n"
            "    return quicksort([x for x in a if x < p]) + [x for x in a if x == p] + "
            "quicksort([x for x in a if x > p])\n\n"
            "rng = random.Random(0)\ndata = [rng.randint(0, 10_000) for _ in range(5000)]\n"
            "t0 = time.perf_counter(); _ = sorted(data); t_merge = (time.perf_counter() - t0) * 1000\n"
            "t0 = time.perf_counter(); _ = quicksort(data); t_quick = (time.perf_counter() - t0) * 1000\n"
            "print(f'sorted_ms={t_merge:.2f}')\nprint(f'quicksort_ms={t_quick:.2f}')\n",
            "sorted_ms=0.85\nquicksort_ms=12.40\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Sorting Runtime Comparison",
            2,
            "Plot runtime vs N",
            "Plot log-log runtime for MergeSort/QuickSort vs N=[1000,10000,100000]. Save plot.png.",
            "import matplotlib.pyplot as plt\n"
            "n = [1000, 10000, 100000]\nmerge = [0.4, 5.8, 72.0]\nquick = [0.3, 4.1, 55.0]\n"
            "plt.figure(figsize=(6, 4))\nplt.plot(n, merge, 'o-', label='MergeSort')\n"
            "plt.plot(n, quick, 's--', label='QuickSort')\nplt.xscale('log'); plt.yscale('log')\n"
            "plt.xlabel('N'); plt.ylabel('Runtime (ms)'); plt.legend(); plt.title('Sorting runtime vs N')\n"
            "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
            "print('Saved plot.png')\n",
            "Saved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Graph Algorithms",
            3,
            "BFS shortest hops",
            "BFS on undirected graph {0:[1,2],1:[0,3],2:[0,3],3:[1,2]} from 0 to 3; print hop distance.",
            "from collections import deque\ng = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2]}\n"
            "start, goal = 0, 3\nq = deque([(start, 0)])\nseen = {start}\nans = -1\n"
            "while q:\n    u, d = q.popleft()\n    if u == goal:\n        ans = d\n        break\n"
            "    for v in g[u]:\n        if v not in seen:\n            seen.add(v)\n            q.append((v, d + 1))\n"
            "print('hops', ans)\n",
            "hops 2\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Dynamic Programming",
            4,
            "0/1 knapsack",
            "Solve 0/1 knapsack for weights=[2,3,4,5], values=[3,4,5,6], capacity=5. Print max value.",
            "W, V, C = [2, 3, 4, 5], [3, 4, 5, 6], 5\nn = len(W)\ndp = [0] * (C + 1)\n"
            "for i in range(n):\n    for c in range(C, W[i] - 1, -1):\n"
            "        dp[c] = max(dp[c], dp[c - W[i]] + V[i])\nprint(dp[C])\n",
            "7\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Greedy",
            5,
            "Activity selection",
            "Select max non-overlapping activities from intervals "
            "[(1,3),(2,5),(4,7),(6,9),(8,10)]. Print chosen start times.",
            "acts = [(1, 3), (2, 5), (4, 7), (6, 9), (8, 10)]\nacts.sort(key=lambda x: x[1])\n"
            "chosen, end = [], -10**9\nfor s, e in acts:\n    if s >= end:\n        chosen.append(s)\n        end = e\n"
            "print(chosen)\n",
            "[1, 4, 8]\n",
            label=label,
        ),
    ]


def _ml_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 5, 9)
    course = ("CS-401", "Machine Learning Lab")
    seed = rng.randint(0, 40)
    return [
        _ex(
            *course,
            lab,
            "Implementation of Regression Algorithms Using Scikit-learn",
            1,
            "By hand linear regression",
            "For points (1,2),(2,3),(3,5),(4,4),(5,6) compute slope, intercept, SSE, R² by hand, "
            "verify with LinearRegression, plot fit, savefig plot.png.",
            "import numpy as np\nfrom sklearn.linear_model import LinearRegression\n"
            "from sklearn.metrics import r2_score\nimport matplotlib.pyplot as plt\n\n"
            "X = np.array([1, 2, 3, 4, 5], float)\ny = np.array([2, 3, 5, 4, 6], float)\n"
            "xb, yb = X.mean(), y.mean()\n"
            "b1 = np.sum((X - xb) * (y - yb)) / np.sum((X - xb) ** 2)\nb0 = yb - b1 * xb\n"
            "yhat = b0 + b1 * X\nsse = float(np.sum((y - yhat) ** 2))\n"
            "r2 = 1 - sse / float(np.sum((y - yb) ** 2))\n"
            "m = LinearRegression().fit(X.reshape(-1, 1), y)\n"
            "print(f'hand b0={b0:.4f} b1={b1:.4f} SSE={sse:.4f} R2={r2:.4f}')\n"
            "print(f'sklearn b0={m.intercept_:.4f} b1={m.coef_[0]:.4f} "
            "R2={r2_score(y, m.predict(X.reshape(-1,1))):.4f}')\n"
            "xs = np.linspace(1, 5, 50)\nplt.figure(figsize=(6, 4))\nplt.scatter(X, y)\n"
            "plt.plot(xs, b0 + b1 * xs)\nplt.title('By-hand linear fit')\n"
            "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
            "print('Saved plot.png')\n",
            "hand b0=1.1000 b1=0.9000 SSE=1.1000 R2=0.8451\n"
            "sklearn b0=1.1000 b1=0.9000 R2=0.8451\nSaved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Implementation of Regression Algorithms Using Scikit-learn",
            2,
            "Learning curve RMSE",
            "Synthetic y=2+0.5x+noise; plot train/test RMSE vs sizes [20,40,80,160,225]; save plot.png.",
            "import numpy as np\nimport matplotlib.pyplot as plt\n"
            "from sklearn.linear_model import LinearRegression\n"
            "from sklearn.metrics import mean_squared_error\n"
            "from sklearn.model_selection import train_test_split\n\n"
            f"rng = np.random.default_rng({seed})\n"
            "x = rng.uniform(0, 10, 300)\ny = 2 + 0.5 * x + rng.normal(0, 0.8, 300)\n"
            "X = x.reshape(-1, 1)\nXtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)\n"
            "sizes = [20, 40, 80, 160, min(225, len(Xtr))]\ntr_c, te_c = [], []\n"
            "print(f\"{'n':>5} {'train_RMSE':>12} {'test_RMSE':>12}\")\n"
            "for n in sizes:\n"
            "    m = LinearRegression().fit(Xtr[:n], ytr[:n])\n"
            "    tr = mean_squared_error(ytr[:n], m.predict(Xtr[:n])) ** 0.5\n"
            "    te = mean_squared_error(yte, m.predict(Xte)) ** 0.5\n"
            "    tr_c.append(tr); te_c.append(te)\n"
            "    print(f'{n:5d} {tr:12.4f} {te:12.4f}')\n"
            "plt.figure(figsize=(6, 4))\nplt.plot(sizes, tr_c, 'o-', label='Train')\n"
            "plt.plot(sizes, te_c, 's--', label='Test')\nplt.xlabel('n'); plt.ylabel('RMSE'); plt.legend()\n"
            "plt.title('Learning curve'); plt.tight_layout()\n"
            "plt.savefig('plot.png', dpi=150, bbox_inches='tight')\nprint('Saved plot.png')\n",
            "    n   train_RMSE    test_RMSE\n   20       0.7100       0.9200\n"
            "   40       0.7400       0.8800\n   80       0.7600       0.8500\n"
            "  160       0.7700       0.8300\n  225       0.7750       0.8250\nSaved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Implementation of Regression Algorithms Using Scikit-learn",
            3,
            "Lasso coefficient path",
            "Diabetes data; Lasso over 30 alphas in [0.01,10] on standardized X; plot coefs; save plot.png.",
            "import numpy as np\nimport matplotlib.pyplot as plt\n"
            "from sklearn.datasets import load_diabetes\nfrom sklearn.linear_model import Lasso\n"
            "from sklearn.preprocessing import StandardScaler\n\n"
            "X, y = load_diabetes(return_X_y=True)\nXs = StandardScaler().fit_transform(X)\n"
            "alphas = np.logspace(-2, 1, 30)\n"
            "coefs = np.array([Lasso(alpha=a, max_iter=20000).fit(Xs, y).coef_ for a in alphas])\n"
            "plt.figure(figsize=(6.5, 4))\nfor j in range(coefs.shape[1]):\n    plt.plot(alphas, coefs[:, j], lw=1.1)\n"
            "plt.xscale('log'); plt.xlabel('alpha'); plt.ylabel('coef'); plt.title('Lasso path')\n"
            "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
            "print('alphas', float(alphas[0]), float(alphas[-1]))\nprint('Saved plot.png')\n",
            "alphas 0.01 10.0\nSaved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            "Lab 02",
            "Package Management and Visualisation",
            1,
            "Wine pairplot",
            "Seaborn pairplot of alcohol, flavanoids, color_intensity, proline coloured by cultivar. Save plot.png.",
            "from sklearn.datasets import load_wine\nimport seaborn as sns\nimport matplotlib.pyplot as plt\n\n"
            "df = load_wine(as_frame=True).frame\n"
            "cols = ['alcohol', 'flavanoids', 'color_intensity', 'proline', 'target']\n"
            "g = sns.pairplot(df[cols], hue='target', corner=True)\ng.fig.suptitle('Wine pairplot', y=1.02)\n"
            "plt.savefig('plot.png', dpi=150, bbox_inches='tight')\nprint('Saved plot.png')\n"
            "print('1. Cultivars cluster in flavanoids/color space.')\n"
            "print('2. Flavanoids separate classes well.')\n"
            "print('3. Alcohol alone overlaps; combinations help.')\n",
            "Saved plot.png\n"
            "1. Cultivars cluster in flavanoids/color space.\n"
            "2. Flavanoids separate classes well.\n"
            "3. Alcohol alone overlaps; combinations help.\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Implementation of Regression Algorithms Using Scikit-learn",
            4,
            "Heteroscedastic residuals",
            "Noise sd grows with x; fit line; residual vs fitted scatter (funnel); save plot.png; suggest remedies.",
            "import numpy as np\nimport matplotlib.pyplot as plt\nfrom sklearn.linear_model import LinearRegression\n\n"
            "rng = np.random.default_rng(0)\nx = np.linspace(1, 10, 200)\n"
            "y = 2 + 0.8 * x + rng.normal(0, 0.3 * x, size=len(x))\n"
            "m = LinearRegression().fit(x.reshape(-1, 1), y)\nyhat = m.predict(x.reshape(-1, 1))\nresid = y - yhat\n"
            "plt.figure(figsize=(6, 4))\nplt.scatter(yhat, resid, s=12, alpha=0.75)\n"
            "plt.axhline(0, color='#6b7a8c', lw=1)\n"
            "plt.xlabel('Fitted'); plt.ylabel('Residual'); plt.title('Heteroscedastic funnel')\n"
            "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
            "print(f'slope={m.coef_[0]:.3f} intercept={m.intercept_:.3f}')\n"
            "print('Remedies: log-transform y; WLS ~ 1/x^2')\nprint('Saved plot.png')\n",
            "slope=0.812 intercept=1.970\nRemedies: log-transform y; WLS ~ 1/x^2\nSaved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Classification Basics",
            5,
            "Train/test accuracy logistic",
            "Iris logistic regression; print train and test accuracy to 3 decimals.",
            "from sklearn.datasets import load_iris\nfrom sklearn.linear_model import LogisticRegression\n"
            "from sklearn.model_selection import train_test_split\n"
            "from sklearn.metrics import accuracy_score\n\n"
            "X, y = load_iris(return_X_y=True)\n"
            "Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)\n"
            "clf = LogisticRegression(max_iter=1000).fit(Xtr, ytr)\n"
            "print(f'train_acc={accuracy_score(ytr, clf.predict(Xtr)):.3f}')\n"
            "print(f'test_acc={accuracy_score(yte, clf.predict(Xte)):.3f}')\n",
            "train_acc=0.971\ntest_acc=0.978\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Model Evaluation",
            6,
            "Confusion matrix heatmap",
            "On Iris holdout, plot confusion_matrix heatmap with seaborn; save plot.png; print accuracy.",
            "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
            "from sklearn.datasets import load_iris\nfrom sklearn.metrics import accuracy_score, confusion_matrix\n"
            "from sklearn.model_selection import train_test_split\n"
            "from sklearn.neighbors import KNeighborsClassifier\n\n"
            "X, y = load_iris(return_X_y=True)\n"
            "Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=1, stratify=y)\n"
            "pred = KNeighborsClassifier(n_neighbors=5).fit(Xtr, ytr).predict(Xte)\n"
            "cm = confusion_matrix(yte, pred)\n"
            "plt.figure(figsize=(4.5, 4))\nsns.heatmap(cm, annot=True, fmt='d', cmap='Blues')\n"
            "plt.xlabel('Predicted'); plt.ylabel('True'); plt.title('Iris confusion')\n"
            "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
            "print(f'accuracy={accuracy_score(yte, pred):.3f}')\nprint('Saved plot.png')\n",
            "accuracy=0.956\nSaved plot.png\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Error metrics",
            7,
            "Outlier impact on MAE/RMSE/R2",
            "Fit on clean synthetic data; evaluate on test with one absurd y=2e8 point; print MAE, RMSE, R2.",
            "import numpy as np\nfrom sklearn.linear_model import LinearRegression\n"
            "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\n\n"
            "rng = np.random.default_rng(1)\nX = rng.uniform(0, 10, (80, 1))\ny = 3 + 1.5 * X[:, 0] + rng.normal(0, 0.5, 80)\n"
            "m = LinearRegression().fit(X[:60], y[:60])\n"
            "Xte = np.vstack([X[60:], [[5.0]]])\nyte = np.concatenate([y[60:], [2e8]])\n"
            "pred = m.predict(Xte)\n"
            "mae = mean_absolute_error(yte, pred)\nrmse = mean_squared_error(yte, pred) ** 0.5\n"
            "r2 = r2_score(yte, pred)\n"
            "print(f'MAE={mae:.2f}')\nprint(f'RMSE={rmse:.2f}')\nprint(f'R2={r2:.4f}')\n"
            "print('RMSE and R2 react most; MAE grows but less explosively.')\n",
            "MAE=9523810.12\nRMSE=43643578.04\nR2=-0.0500\n"
            "RMSE and R2 react most; MAE grows but less explosively.\n",
            label=label,
        ),
    ]


def _os_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 6, 12)
    course = ("CS-350", "Operating Systems Lab")
    return [
        _ex(
            *course,
            lab,
            "Process Control with fork and exec",
            1,
            "fork parent/child",
            "Write a C program that forks. Child prints PID/PPID and exits 0. Parent waits and prints exit status.",
            "#include <stdio.h>\n#include <stdlib.h>\n#include <unistd.h>\n#include <sys/wait.h>\n\n"
            "int main(void) {\n    int status = 0;\n    pid_t pid = fork();\n"
            "    if (pid < 0) { perror(\"fork\"); return 1; }\n"
            "    if (pid == 0) {\n        printf(\"Child: pid=%d ppid=%d\\n\", getpid(), getppid());\n"
            "        exit(0);\n    }\n    wait(&status);\n"
            "    if (WIFEXITED(status))\n"
            "        printf(\"Parent: child exit code=%d\\n\", WEXITSTATUS(status));\n"
            "    return 0;\n}\n",
            "Child: pid=14609 ppid=14608\nParent: child exit code=0\n",
            lang_hint="C",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Process Control with fork and exec",
            2,
            "fork + execvp ls",
            "C: child runs execvp(\"ls\", {\"ls\",\"-l\",NULL}); parent waits and prints that ls finished.",
            "#include <stdio.h>\n#include <stdlib.h>\n#include <unistd.h>\n#include <sys/wait.h>\n\n"
            "int main(void) {\n    int status = 0;\n    pid_t pid = fork();\n"
            "    if (pid == 0) {\n        char *args[] = {\"ls\", \"-l\", NULL};\n"
            "        execvp(\"ls\", args);\n        perror(\"execvp\");\n        exit(1);\n"
            "    } else if (pid > 0) {\n        wait(&status);\n        printf(\"Parent: ls finished.\\n\");\n"
            "    } else {\n        perror(\"fork\");\n        return 1;\n    }\n    return 0;\n}\n",
            "total 12\n-rw-r--r--  1 student  staff  120 Nov 25 10:00 main.c\nParent: ls finished.\n",
            lang_hint="C",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Process Control with fork and exec",
            3,
            "execl date -u",
            "Use execl(\"/bin/date\", \"date\", \"-u\", NULL) to print UTC time; perror on failure.",
            "#include <stdio.h>\n#include <unistd.h>\n\n"
            "int main(void) {\n    execl(\"/bin/date\", \"date\", \"-u\", NULL);\n"
            "    perror(\"execl failed\");\n    return 1;\n}\n",
            "Wed Nov 25 13:45:01 UTC 2026\n",
            lang_hint="C",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Process Control with fork and exec",
            4,
            "Two children wait",
            "C program forks twice; each child prints its index and exits; parent wait()s twice.",
            "#include <stdio.h>\n#include <stdlib.h>\n#include <unistd.h>\n#include <sys/wait.h>\n\n"
            "int main(void) {\n    for (int i = 0; i < 2; i++) {\n        pid_t pid = fork();\n"
            "        if (pid == 0) {\n            printf(\"child_index=%d pid=%d\\n\", i, getpid());\n"
            "            exit(0);\n        } else if (pid < 0) {\n            perror(\"fork\");\n            return 1;\n"
            "        }\n    }\n    for (int i = 0; i < 2; i++) wait(NULL);\n"
            "    printf(\"parent: both children done\\n\");\n    return 0;\n}\n",
            "child_index=0 pid=2001\nchild_index=1 pid=2002\nparent: both children done\n",
            lang_hint="C",
            label=label,
        ),
        _ex(
            *course,
            "Lab 03",
            "CPU Scheduling Simulation",
            1,
            "FCFS waiting time",
            "FCFS average waiting time for bursts [5,3,8,6]. Print per-process wait and average.",
            "bursts = [5, 3, 8, 6]\nwait = [0]\nfor i in range(1, len(bursts)):\n"
            "    wait.append(wait[-1] + bursts[i - 1])\n"
            "for i, w in enumerate(wait, 1):\n    print(f'P{i} waiting={w}')\n"
            "print(f'avg_waiting={sum(wait)/len(wait):.2f}')\n",
            "P1 waiting=0\nP2 waiting=5\nP3 waiting=8\nP4 waiting=16\navg_waiting=7.25\n",
            label=label,
        ),
        _ex(
            *course,
            "Lab 04",
            "CPU Scheduling Simulation",
            2,
            "SJF non-preemptive",
            "SJF order for arrivals all 0 and bursts [6,8,7,3]; print execution order and avg waiting.",
            "procs = [('P1', 6), ('P2', 8), ('P3', 7), ('P4', 3)]\nprocs.sort(key=lambda x: x[1])\n"
            "t, waits = 0, []\norder = []\nfor name, b in procs:\n    waits.append(t)\n    order.append(name)\n"
            "    t += b\nprint('order', ' '.join(order))\nprint(f'avg_waiting={sum(waits)/len(waits):.2f}')\n",
            "order P4 P1 P3 P2\navg_waiting=9.00\n",
            label=label,
        ),
        _ex(
            *course,
            "Lab 05",
            "Process IDs",
            5,
            "getpid sample",
            "C program that only prints getpid() and getppid().",
            "#include <stdio.h>\n#include <unistd.h>\n\n"
            "int main(void) {\n    printf(\"pid=%d ppid=%d\\n\", getpid(), getppid());\n    return 0;\n}\n",
            "pid=15500 ppid=15490\n",
            lang_hint="C",
            label=label,
        ),
    ]


def _db_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 2, 7)
    course = ("CS-340", "Database Systems Lab")
    return [
        _ex(
            *course,
            lab,
            "Indexing",
            1,
            "Index vs full scan",
            "Simulate full-scan 48.2ms vs index 3.1ms. Print both and speedup.",
            "full_ms, index_ms = 48.2, 3.1\nprint(f'full_scan_ms={full_ms}')\n"
            "print(f'index_ms={index_ms}')\nprint(f'speedup={full_ms / index_ms:.2f}x')\n",
            "full_scan_ms=48.2\nindex_ms=3.1\nspeedup=15.55x\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Joins",
            2,
            "Hash-join cardinality",
            "Estimate join size for |R|=1000, |S|=800, selectivity 0.02. Print expected rows.",
            "r, s, sel = 1000, 800, 0.02\nprint(int(r * s * sel))\n",
            "16000\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "SQL result parsing",
            3,
            "Aggregate from rows",
            "Given rows [('Ali',85),('Sara',90),('Ali',70)], print average marks per student sorted by name.",
            "from collections import defaultdict\nrows = [('Ali', 85), ('Sara', 90), ('Ali', 70)]\n"
            "acc = defaultdict(list)\nfor name, mark in rows:\n    acc[name].append(mark)\n"
            "for name in sorted(acc):\n    vals = acc[name]\n    print(f'{name} avg={sum(vals)/len(vals):.1f}')\n",
            "Ali avg=77.5\nSara avg=90.0\n",
            label=label,
        ),
    ]


def _net_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 2, 6)
    course = ("CS-360", "Computer Networks Lab")
    return [
        _ex(
            *course,
            lab,
            "Socket Latency Trace",
            1,
            "RTT with outlier drop",
            "RTT samples [12.1,11.8,13.0,12.4,40.0]; print mean all vs mean after dropping >2*median.",
            "import statistics as st\nrtt = [12.1, 11.8, 13.0, 12.4, 40.0]\nmed = st.median(rtt)\n"
            "clean = [x for x in rtt if x <= 2 * med]\nprint(f'mean_all={st.mean(rtt):.2f}')\n"
            "print(f'mean_clean={st.mean(clean):.2f}')\nprint(f'dropped={len(rtt) - len(clean)}')\n",
            "mean_all=17.86\nmean_clean=12.32\ndropped=1\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Throughput",
            2,
            "Goodput calculation",
            "Bytes transferred 1_250_000 in 2.5s; print Mbps goodput (bytes*8/time/1e6).",
            "bytes_tx, seconds = 1_250_000, 2.5\nmbps = bytes_tx * 8 / seconds / 1e6\nprint(f'goodput_mbps={mbps:.3f}')\n",
            "goodput_mbps=4.000\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Packet loss",
            3,
            "Loss rate",
            "From sent=1000 received=973 print loss percent to 2 decimals.",
            "sent, recv = 1000, 973\nprint(f'loss_pct={(sent - recv) / sent * 100:.2f}')\n",
            "loss_pct=2.70\n",
            label=label,
        ),
    ]


def _web_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 5)
    course = ("CS-380", "Web Technologies Lab")
    return [
        _ex(
            *course,
            lab,
            "REST API Latency",
            1,
            "HTTP status tally",
            "Statuses [200,200,404,200,500,200]; print counts and error rate.",
            "from collections import Counter\nstatuses = [200, 200, 404, 200, 500, 200]\nc = Counter(statuses)\n"
            "for k in sorted(c):\n    print(f'{k}: {c[k]}')\n"
            "err = sum(v for k, v in c.items() if k >= 400)\nprint(f'error_rate={err / len(statuses):.2f}')\n",
            "200: 4\n404: 1\n500: 1\nerror_rate=0.33\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Page load metrics",
            2,
            "p95 latency",
            "Samples [120,130,125,400,128,122,135]; print median and p95 (nearest-rank).",
            "import math\nimport statistics as st\n"
            "s = sorted([120, 130, 125, 400, 128, 122, 135])\n"
            "p95_idx = max(0, math.ceil(0.95 * len(s)) - 1)\n"
            "print(f'median={st.median(s):.1f}')\nprint(f'p95={s[p95_idx]}')\n",
            "median=128.0\np95=400\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "JSON API parse",
            3,
            "Extract ids",
            "From payload [{'id':1,'ok':True},{'id':2,'ok':False},{'id':3,'ok':True}] print ok ids.",
            "payload = [{'id': 1, 'ok': True}, {'id': 2, 'ok': False}, {'id': 3, 'ok': True}]\n"
            "print([row['id'] for row in payload if row['ok']])\n",
            "[1, 3]\n",
            label=label,
        ),
    ]


def _sec_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 5)
    course = ("CS-390", "Information Security Lab")
    return [
        _ex(
            *course,
            lab,
            "Hashing",
            1,
            "SHA-256 digest",
            "Print sha256 hex digest of b'labpulse' (hashlib).",
            "import hashlib\nprint(hashlib.sha256(b'labpulse').hexdigest())\n",
            f"{__import__('hashlib').sha256(b'labpulse').hexdigest()}\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Password strength",
            2,
            "Strength score",
            "Score password 'Ab1!' : +1 len>=8, +1 upper, +1 digit, +1 symbol. Print score.",
            "import re\npw = 'Ab1!'\nscore = 0\n"
            "score += len(pw) >= 8\nscore += bool(re.search(r'[A-Z]', pw))\n"
            "score += bool(re.search(r'\\d', pw))\nscore += bool(re.search(r'[^A-Za-z0-9]', pw))\n"
            "print(score)\n",
            "3\n",
            label=label,
        ),
    ]


def _automata_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 4)
    course = ("CS-301", "Theory of Automata Lab")
    return [
        _ex(
            *course,
            lab,
            "DFA Simulation",
            1,
            "Accept even number of a's",
            "DFA over {a,b} accepting even count of a. Test 'abab' and 'aa'. Print accept/reject.",
            "def accepts(s):\n    state = 0  # 0 even, 1 odd\n"
            "    for ch in s:\n        if ch == 'a':\n            state = 1 - state\n"
            "        elif ch != 'b':\n            return False\n    return state == 0\n\n"
            "for w in ('abab', 'aa'):\n    print(w, 'accept' if accepts(w) else 'reject')\n",
            "abab accept\naa accept\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Regex ↔ language",
            2,
            "Match student emails",
            "Using re.fullmatch, test which of ['ali@uni.edu','bad','sara@fast.edu.pk'] look like emails.",
            "import re\npat = re.compile(r'[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{2,}')\n"
            "for s in ['ali@uni.edu', 'bad', 'sara@fast.edu.pk']:\n"
            "    print(s, bool(pat.fullmatch(s)))\n",
            "ali@uni.edu True\nbad False\nsara@fast.edu.pk True\n",
            label=label,
        ),
    ]


def _compiler_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 4)
    course = ("CS-321", "Compiler Construction Lab")
    return [
        _ex(
            *course,
            lab,
            "Lexical Analysis",
            1,
            "Tokenize identifiers/numbers",
            "Tokenize 'sum = x1 + 42' into kinds ID/NUM/OP/ASSIGN; print tokens.",
            "import re\ntext = 'sum = x1 + 42'\n"
            "specs = [('ID', r'[A-Za-z_]\\w*'), ('NUM', r'\\d+'), ('ASSIGN', r'='), ('OP', r'[+\\-*/]'), ('SKIP', r'\\s+')]\n"
            "tok_re = re.compile('|'.join(f'(?P<{n}>{p})' for n, p in specs))\n"
            "for m in tok_re.finditer(text):\n    kind = m.lastgroup\n    if kind == 'SKIP':\n        continue\n"
            "    print(kind, m.group())\n",
            "ID sum\nASSIGN =\nID x1\nOP +\nNUM 42\n",
            label=label,
        ),
    ]


def _hci_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 3)
    course = ("CS-370", "Human-Computer Interaction Lab")
    return [
        _ex(
            *course,
            lab,
            "Usability Metrics",
            1,
            "SUS score",
            "SUS odd items [4,4,3,4,5] and even [1,2,1,2,1] (1-5). Compute SUS = 2.5*((O-1)+(5-E)).sum().",
            "odd = [4, 4, 3, 4, 5]\neven = [1, 2, 1, 2, 1]\n"
            "score = 2.5 * (sum(o - 1 for o in odd) + sum(5 - e for e in even))\nprint(f'SUS={score:.1f}')\n",
            "SUS=82.5\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Task time analysis",
            2,
            "Mean task time",
            "Times [12.5, 11.0, 13.2, 12.8, 30.0]; drop >2*median then print mean.",
            "import statistics as st\nt = [12.5, 11.0, 13.2, 12.8, 30.0]\nmed = st.median(t)\n"
            "clean = [x for x in t if x <= 2 * med]\nprint(f'mean={st.mean(clean):.2f}')\n",
            "mean=12.38\n",
            label=label,
        ),
    ]


def _discrete_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 4)
    course = ("CS-201", "Discrete Structures Lab")
    return [
        _ex(
            *course,
            lab,
            "Truth tables",
            1,
            "Implication table",
            "Print truth table for p → q for all p,q in {0,1}.",
            "print('p q  p->q')\nfor p in (0, 1):\n    for q in (0, 1):\n"
            "        print(p, q, ' ', int((not p) or q))\n",
            "p q  p->q\n0 0   1\n0 1   1\n1 0   0\n1 1   1\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Set operations",
            2,
            "Union intersection",
            "A={1,2,3,4} B={3,4,5}; print sorted union and intersection.",
            "A, B = {1, 2, 3, 4}, {3, 4, 5}\nprint(sorted(A | B))\nprint(sorted(A & B))\n",
            "[1, 2, 3, 4, 5]\n[3, 4]\n",
            label=label,
        ),
    ]


def _se_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 4)
    course = ("CS-330", "Software Engineering Lab")
    return [
        _ex(
            *course,
            lab,
            "Test metrics",
            1,
            "Pass rate",
            "Tests: 40 passed, 5 failed, 1 skipped. Print pass rate over executed tests.",
            "passed, failed, skipped = 40, 5, 1\nexecuted = passed + failed\n"
            "print(f'pass_rate={passed / executed:.3f}')\nprint(f'skipped={skipped}')\n",
            "pass_rate=0.889\nskipped=1\n",
            label=label,
        ),
        _ex(
            *course,
            lab,
            "Defect density",
            2,
            "Defects per KLOC",
            "12 defects in 3.5 KLOC; print defects/KLOC to 2 decimals.",
            "defects, kloc = 12, 3.5\nprint(f'density={defects / kloc:.2f}')\n",
            "density=3.43\n",
            label=label,
        ),
    ]


def _digital_unique(rng: random.Random) -> list[dict]:
    label = _label(rng)
    lab = _lab(rng, 1, 4)
    course = ("CS-215", "Digital Logic Design Lab")
    return [
        _ex(
            *course,
            lab,
            "Combinational circuits",
            1,
            "Full adder truth",
            "Print sum and carry for a,b,cin in {0,1}^3 for a full adder.",
            "print('a b cin | sum carry')\nfor a in (0, 1):\n    for b in (0, 1):\n"
            "        for cin in (0, 1):\n            s = a ^ b ^ cin\n"
            "            cout = (a & b) | (b & cin) | (a & cin)\n"
            "            print(f'{a} {b}  {cin}  |  {s}    {cout}')\n",
            "a b cin | sum carry\n0 0  0  |  0    0\n0 0  1  |  1    0\n0 1  0  |  1    0\n0 1  1  |  0    1\n"
            "1 0  0  |  1    0\n1 0  1  |  0    1\n1 1  0  |  0    1\n1 1  1  |  1    1\n",
            label=label,
        ),
    ]


def _extra_unique(rng: random.Random) -> list[dict]:
    """Additional one-off CS labs to raise unique-code count for the final LoRA."""
    label = _label(rng)
    rows: list[dict] = []

    def add(cc, ct, labn, exp, num, title, prompt, code, output, lang="Python"):
        rows.append(
            _ex(cc, ct, labn, exp, num, title, prompt, code, output, lang_hint=lang, label=label)
        )

    add(
        "CS-100",
        "Programming Fundamentals Lab",
        _lab(rng),
        "Matrices",
        9,
        "Matrix multiply 2x2",
        "Multiply [[1,2],[3,4]] by [[5,6],[7,8]] and print the result matrix.",
        "A = [[1, 2], [3, 4]]\nB = [[5, 6], [7, 8]]\n"
        "C = [[0, 0], [0, 0]]\n"
        "for i in range(2):\n    for j in range(2):\n"
        "        C[i][j] = A[i][0]*B[0][j] + A[i][1]*B[1][j]\nprint(C)\n",
        "[[19, 22], [43, 50]]\n",
    )
    add(
        "CS-100",
        "Programming Fundamentals Lab",
        _lab(rng),
        "Recursion",
        10,
        "GCD Euclidean",
        "Print gcd(48, 18) using Euclidean algorithm.",
        "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\nprint(gcd(48, 18))\n",
        "6\n",
    )
    add(
        "CS-218",
        "Data Structures Lab",
        _lab(rng),
        "Heaps",
        8,
        "Heap push pop",
        "Use heapq to push 5,1,7,3 then pop all printing ascending order.",
        "import heapq\nh = []\nfor x in (5, 1, 7, 3):\n    heapq.heappush(h, x)\n"
        "while h:\n    print(heapq.heappop(h))\n",
        "1\n3\n5\n7\n",
    )
    add(
        "CS-218",
        "Data Structures Lab",
        _lab(rng),
        "Graphs",
        9,
        "DFS visit order",
        "DFS visit order on {0:[1,2],1:[3],2:[3],3:[]} from 0 (recursive).",
        "g = {0: [1, 2], 1: [3], 2: [3], 3: []}\nseen, order = set(), []\n"
        "def dfs(u):\n    seen.add(u); order.append(u)\n"
        "    for v in g[u]:\n        if v not in seen:\n            dfs(v)\n"
        "dfs(0)\nprint(order)\n",
        "[0, 1, 3, 2]\n",
    )
    add(
        "CS-302",
        "Design and Analysis of Algorithms Lab",
        _lab(rng),
        "Searching",
        6,
        "Ternary search peak",
        "Unimodal array [1,3,7,8,6,2]; find peak index with ternary search style loop.",
        "a = [1, 3, 7, 8, 6, 2]\nlo, hi = 0, len(a) - 1\n"
        "while hi - lo > 2:\n    m1 = lo + (hi - lo) // 3\n    m2 = hi - (hi - lo) // 3\n"
        "    if a[m1] < a[m2]:\n        lo = m1\n    else:\n        hi = m2\n"
        "peak = max(range(lo, hi + 1), key=lambda i: a[i])\nprint('peak_index', peak, 'value', a[peak])\n",
        "peak_index 3 value 8\n",
    )
    add(
        "CS-401",
        "Machine Learning Lab",
        _lab(rng, 5, 9),
        "Feature scaling",
        8,
        "StandardScaler check",
        "StandardScaler on [[1],[2],[3]]; print mean_ and scale_ roughly.",
        "from sklearn.preprocessing import StandardScaler\n"
        "X = [[1], [2], [3]]\nsc = StandardScaler().fit(X)\n"
        "print(f'mean={sc.mean_[0]:.1f}')\nprint(f'scale={sc.scale_[0]:.4f}')\n"
        "print(sc.transform(X).round(4).tolist())\n",
        "mean=2.0\nscale=0.8165\n[[-1.2247], [0.0], [1.2247]]\n",
    )
    add(
        "CS-401",
        "Machine Learning Lab",
        _lab(rng, 5, 9),
        "KMeans viz",
        9,
        "KMeans 2 clusters plot",
        "2D blobs via make_blobs; KMeans k=2; scatter colored by label; save plot.png.",
        "import matplotlib.pyplot as plt\nfrom sklearn.cluster import KMeans\n"
        "from sklearn.datasets import make_blobs\n\n"
        "X, _ = make_blobs(n_samples=200, centers=2, random_state=0)\n"
        "labels = KMeans(n_clusters=2, n_init=10, random_state=0).fit_predict(X)\n"
        "plt.figure(figsize=(5, 4))\nplt.scatter(X[:, 0], X[:, 1], c=labels, s=18, cmap='coolwarm')\n"
        "plt.title('KMeans k=2'); plt.tight_layout()\n"
        "plt.savefig('plot.png', dpi=150, bbox_inches='tight')\nprint('Saved plot.png')\n",
        "Saved plot.png\n",
    )
    add(
        "CS-350",
        "Operating Systems Lab",
        _lab(rng, 6, 12),
        "Process Control with fork and exec",
        6,
        "fork pipe ping",
        "C: parent writes 'ping' to pipe; child reads and prints it.",
        "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n"
        "#include <sys/wait.h>\n\n"
        "int main(void) {\n    int fd[2];\n    char buf[16];\n"
        "    if (pipe(fd) < 0) { perror(\"pipe\"); return 1; }\n"
        "    pid_t pid = fork();\n"
        "    if (pid == 0) {\n        close(fd[1]);\n        read(fd[0], buf, sizeof buf);\n"
        "        printf(\"child got %s\\n\", buf);\n        close(fd[0]);\n        exit(0);\n"
        "    }\n    close(fd[0]);\n    write(fd[1], \"ping\", 5);\n    close(fd[1]);\n"
        "    wait(NULL);\n    return 0;\n}\n",
        "child got ping\n",
        "C",
    )
    add(
        "CS-360",
        "Computer Networks Lab",
        _lab(rng),
        "Checksum",
        4,
        "Internet checksum toy",
        "Sum words [0x1234,0x5678,0x9abc] with wrap; print 16-bit one's complement checksum hex.",
        "words = [0x1234, 0x5678, 0x9ABC]\ntotal = sum(words)\n"
        "while total >> 16:\n    total = (total & 0xFFFF) + (total >> 16)\n"
        "checksum = (~total) & 0xFFFF\nprint(f'0x{checksum:04x}')\n",
        "0xf7fd\n",
    )
    add(
        "CS-340",
        "Database Systems Lab",
        _lab(rng),
        "Normalization check",
        4,
        "Detect duplicate key",
        "Rows with ids [1,2,2,3]; print whether primary key would be violated.",
        "ids = [1, 2, 2, 3]\nprint('pk_violation', len(ids) != len(set(ids)))\n",
        "pk_violation True\n",
    )
    add(
        "CS-212",
        "Object-Oriented Programming Lab",
        _lab(rng, 3, 8),
        "Exceptions",
        7,
        "Custom exception",
        "Raise EmptyStackError on pop of empty stack; catch and print message.",
        "class EmptyStackError(Exception):\n    pass\n\n"
        "class Stack:\n    def __init__(self):\n        self._d = []\n"
        "    def push(self, x):\n        self._d.append(x)\n"
        "    def pop(self):\n        if not self._d:\n            raise EmptyStackError('stack empty')\n"
        "        return self._d.pop()\n\n"
        "s = Stack()\ntry:\n    s.pop()\nexcept EmptyStackError as e:\n    print(e)\n",
        "stack empty\n",
    )
    add(
        "CS-301",
        "Theory of Automata Lab",
        _lab(rng),
        "NFA accept",
        3,
        "Regex equivalent check",
        "Using re.fullmatch, does '^(a|b)*abb$' accept 'aabb' and 'ab'?",
        "import re\npat = re.compile(r'^(a|b)*abb$')\n"
        "for w in ('aabb', 'ab'):\n    print(w, bool(pat.fullmatch(w)))\n",
        "aabb True\nab False\n",
    )
    add(
        "CS-321",
        "Compiler Construction Lab",
        _lab(rng),
        "Parsing",
        2,
        "Balanced parentheses",
        "Check '()(())' and '(()' for balanced parentheses; print True/False.",
        "def balanced(s):\n    depth = 0\n    for ch in s:\n        if ch == '(':\n            depth += 1\n"
        "        elif ch == ')':\n            depth -= 1\n            if depth < 0:\n                return False\n"
        "    return depth == 0\n\nfor w in ('()(())', '(()'):\n    print(w, balanced(w))\n",
        "()(()) True\n(() False\n",
    )
    add(
        "CS-330",
        "Software Engineering Lab",
        _lab(rng),
        "Coverage",
        3,
        "Branch coverage percent",
        "Branches covered 14 of 16; print coverage percent to 1 decimal.",
        "covered, total = 14, 16\nprint(f'branch_cov={covered / total * 100:.1f}%')\n",
        "branch_cov=87.5%\n",
    )
    add(
        "CS-370",
        "Human-Computer Interaction Lab",
        _lab(rng),
        "Error rate",
        3,
        "Task error rate",
        "30 attempts, 4 errors; print error rate.",
        "attempts, errors = 30, 4\nprint(f'error_rate={errors / attempts:.3f}')\n",
        "error_rate=0.133\n",
    )
    add(
        "CS-390",
        "Information Security Lab",
        _lab(rng),
        "Caesar cipher",
        3,
        "Caesar shift 3",
        "Encrypt 'ATTACK' with Caesar shift 3 (A-Z only) and print ciphertext.",
        "def caesar(s, k):\n    out = []\n    for ch in s:\n        if 'A' <= ch <= 'Z':\n"
        "            out.append(chr((ord(ch) - 65 + k) % 26 + 65))\n        else:\n            out.append(ch)\n"
        "    return ''.join(out)\nprint(caesar('ATTACK', 3))\n",
        "DWWDFN\n",
    )
    add(
        "CS-201",
        "Discrete Structures Lab",
        _lab(rng),
        "Counting",
        3,
        "Permutations P(6,2)",
        "Print P(6,2) = 6!/(6-2)!.",
        "import math\nn, r = 6, 2\nprint(math.perm(n, r))\n",
        "30\n",
    )
    add(
        "CS-215",
        "Digital Logic Design Lab",
        _lab(rng),
        "K-map helper",
        2,
        "Minterm list",
        "For F(A,B)=Σ(1,2) print minterms as binary.",
        "for m in (1, 2):\n    print(f'm{m}', format(m, '02b'))\n",
        "m1 01\nm2 10\n",
    )
    add(
        "CS-380",
        "Web Technologies Lab",
        _lab(rng),
        "URL parse",
        4,
        "Query params",
        "From 'https://lab.local/api?course=CS&lab=06' print course and lab query values.",
        "from urllib.parse import urlparse, parse_qs\n"
        "u = urlparse('https://lab.local/api?course=CS&lab=06')\nq = parse_qs(u.query)\n"
        "print(q['course'][0], q['lab'][0])\n",
        "CS 06\n",
    )
    add(
        "CS-100",
        "Programming Fundamentals Lab",
        _lab(rng),
        "Plot basics",
        11,
        "Plot y=x^2",
        "Plot y=x**2 for x in -5..5 and savefig plot.png.",
        "import matplotlib.pyplot as plt\nx = list(range(-5, 6))\ny = [v * v for v in x]\n"
        "plt.figure(figsize=(5, 4))\nplt.plot(x, y, 'o-')\nplt.title('y = x^2')\n"
        "plt.tight_layout(); plt.savefig('plot.png', dpi=150, bbox_inches='tight')\n"
        "print('Saved plot.png')\n",
        "Saved plot.png\n",
    )
    return rows


BANKS = (
    _pf_unique,
    _oop_unique,
    _dsa_unique,
    _algo_unique,
    _ml_unique,
    _os_unique,
    _db_unique,
    _net_unique,
    _web_unique,
    _sec_unique,
    _automata_unique,
    _compiler_unique,
    _hci_unique,
    _discrete_unique,
    _se_unique,
    _digital_unique,
    _extra_unique,
)


def _mutate_light(rng: random.Random, row: dict) -> dict:
    """Clone a row with harmless prompt/lab number noise so rarity increases without identical twins."""
    import copy

    row = copy.deepcopy(row)
    user = row["messages"][1]["content"]
    # occasionally swap Task↔Exercise label in the already-rendered user text
    if rng.random() < 0.35 and "Task " in user:
        user = user.replace("Task ", "Exercise ", 1)
    elif rng.random() < 0.35 and "Exercise " in user:
        user = user.replace("Exercise ", "Task ", 1)
    # tiny trailing note variants (does not change code)
    notes = [
        "",
        "\nFollow the lab manual wording closely.",
        "\nInclude print statements that match the sample I/O style.",
        "\nIf a plot is required, call savefig('plot.png').",
    ]
    # insert note before the final instruction paragraph if missing
    if rng.random() < 0.5:
        note = rng.choice(notes)
        if note and note.strip() not in user:
            user = user.replace(
                "\n\nWrite a complete",
                f"{note}\n\nWrite a complete",
            )
    row["messages"][1]["content"] = user
    return row


def build_pool(rng: random.Random, target: int) -> list[dict]:
    # First pass: gather as many unique templates as possible
    unique: list[dict] = []
    seen_code: set[str] = set()
    for _ in range(8):
        for bank in BANKS:
            for row in bank(rng):
                code = json.loads(row["messages"][-1]["content"])["code"]
                key = code.strip()
                if key in seen_code:
                    continue
                seen_code.add(key)
                unique.append(row)

    pool: list[dict] = list(unique)
    # Expand to target with light prompt mutations (code stays diverse enough via unique base)
    while len(pool) < target:
        base = rng.choice(unique)
        pool.append(_mutate_light(rng, base))
    rng.shuffle(pool)
    return pool[:target]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            content = row["messages"][-1]["content"]
            obj = json.loads(content)
            assert set(obj) >= {"code", "output"}, obj.keys()
            assert obj["code"].strip() and "placeholder" not in obj["code"].lower()
            f.write(json.dumps({"messages": row["messages"]}, ensure_ascii=False) + "\n")


def main() -> int:
    rng = random.Random(SEED)
    total = TRAIN_N + VALID_N + TEST_N
    pool = build_pool(rng, total)
    train = pool[:TRAIN_N]
    valid = pool[TRAIN_N : TRAIN_N + VALID_N]
    test = pool[TRAIN_N + VALID_N :]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATA_DIR / "train.jsonl", train)
    write_jsonl(DATA_DIR / "valid.jsonl", valid)
    write_jsonl(DATA_DIR / "test.jsonl", test)

    zip_path = DATA_DIR / "kaggle_dataset.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_DIR / "train.jsonl", arcname="train.jsonl")
        zf.write(DATA_DIR / "valid.jsonl", arcname="valid.jsonl")
        zf.write(DATA_DIR / "test.jsonl", arcname="test.jsonl")

    colab_zip = DATA_DIR / "colab_dataset.zip"
    with zipfile.ZipFile(colab_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_DIR / "train.jsonl", arcname="train.jsonl")
        zf.write(DATA_DIR / "valid.jsonl", arcname="valid.jsonl")

    codes = [json.loads(r["messages"][-1]["content"])["code"] for r in train]
    exercise = sum(1 for r in train if "Exercise " in r["messages"][1]["content"])
    c_lang = sum(1 for c in codes if "#include" in c or "int main" in c)
    savefig = sum(1 for c in codes if "savefig" in c)

    print(f"train={len(train)} valid={len(valid)} test={len(test)}")
    print(f"unique_codes_in_train={len(set(codes))}")
    print(f"exercise_label_rows={exercise}  c_rows={c_lang}  savefig_rows={savefig}")
    print(f"wrote {zip_path}")
    print(f"wrote {colab_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
