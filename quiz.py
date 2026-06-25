# -*- coding: utf-8 -*-
import re
import random
import sys
from typing import List, Dict

QUESTION_TYPES = {
    "single": ("\u5355\u9009\u9898", 40),
    "multi": ("\u591a\u9009\u9898", 20),
    "judge": ("\u5224\u65ad\u9898", 20),
}


def load_questions() -> tuple:
    with open(r"马克思主义基本原理题库.txt", "rb") as f:
        raw = f.read()
    html = raw.decode("gbk", errors="replace")

    m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    if not m:
        raise Exception("\u65e0\u6cd5\u89e3\u6790\u6587\u6863")
    body = m.group(1)
    text = re.sub(r"<[^>]+>", "", body)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = text.splitlines()
    q_re = re.compile(r"^(\d+)[\u3001\uff0e.]\s*(.*)")
    a_re = re.compile(r"\u7b54\u6848[\uff1a:]\s*(.+?)$")
    opt_re = re.compile(r"^([A-Da-d])[\u3001\uff0e.]\s*(.*)")

    singles, multis, judges = [], [], []
    cur_num, cur_q, cur_opts, cur_ans = None, None, [], None

    for line in lines:
        s = line.strip()
        if not s:
            continue

        qm = q_re.match(s)
        if qm:
            _save(cur_num, cur_q, cur_opts, cur_ans, singles, multis, judges)
            cur_num = int(qm.group(1))
            cur_q = qm.group(2)
            cur_opts, cur_ans = [], None
            continue

        am = a_re.match(s)
        if am:
            cur_ans = am.group(1).strip()
            continue

        om = opt_re.match(s)
        if om:
            cur_opts.append(s)
        elif cur_q:
            cur_q += " " + s

    _save(cur_num, cur_q, cur_opts, cur_ans, singles, multis, judges)
    return singles, multis, judges


def _save(num, question, opts, answer, singles, multis, judges):
    if num is None or not question or answer is None:
        return
    q = {"num": num, "question": question, "options": opts, "answer": answer}
    if answer in ("\u6b63\u786e", "\u9519\u8bef"):
        judges.append(q)
    elif len(answer) > 1:
        multis.append(q)
    else:
        singles.append(q)


def pick(questions, count):
    return random.sample(questions, min(count, len(questions)))


def check(user, correct):
    s1 = (
        user.strip()
        .upper()
        .replace("\uff0c", ",")
        .replace(" ", "")
        .replace("\u3001", ",")
    )
    s2 = (
        correct.strip()
        .upper()
        .replace("\uff0c", ",")
        .replace(" ", "")
        .replace("\u3001", ",")
    )
    return "".join(sorted(s1.split(","))) == "".join(sorted(s2.split(",")))


def run(questions):
    total = len(questions)
    correct = 0
    border = "=" * 60

    for i, q in enumerate(questions, 1):
        if q["answer"] in ("\u6b63\u786e", "\u9519\u8bef"):
            tname = "\u5224\u65ad\u9898"
        elif len(q["answer"]) > 1:
            tname = "\u591a\u9009\u9898"
        else:
            tname = "\u5355\u9009\u9898"

        print()
        print(border)
        print(tname + " " + str(i) + "/" + str(total) + " \u9898")
        print(q["question"])

        if tname == "\u5224\u65ad\u9898":
            print("  A. \u6b63\u786e")
            print("  B. \u9519\u8bef")
        else:
            for o in q["options"]:
                print("  " + o)
            if tname == "\u591a\u9009\u9898":
                print("(\u53ef\u8f93\u5165\u591a\u4e2a\u9009\u9879\uff0c\u5982 ABC)")

        while True:
            try:
                ans = input("\n\u8f93\u5165\u7b54\u6848: ").strip()
                if ans:
                    break
            except (EOFError, KeyboardInterrupt):
                print("\n\u9000\u51fa\u3002")
                sys.exit(0)

        ok = check(ans, q["answer"])
        if ok:
            print("  [OK] \u56de\u7b54\u6b63\u786e\uff01")
            correct += 1
        else:
            print("  [X] \u6b63\u786e\u7b54\u6848: " + q["answer"])

    print()
    print(border)
    print("\u8003\u8bd5\u7ed3\u675f\uff01")
    print("\u603b\u9898\u6570: " + str(total))
    print("\u6b63\u786e\u6570: " + str(correct))
    print("\u6b63\u786e\u7387: " + f"{correct / total * 100:.1f}%")
    input("\n\u6309\u56de\u8f66\u952e\u9000\u51fa...")


def main():
    random.seed()
    print("\u52a0\u8f7d\u9898\u5e93...", end="", flush=True)
    try:
        singles, multis, judges = load_questions()
        print(" OK")
        print("  \u5355\u9009\u9898: " + str(len(singles)))
        print("  \u591a\u9009\u9898: " + str(len(multis)))
        print("  \u5224\u65ad\u9898: " + str(len(judges)))
    except Exception as e:
        print("\n\u52a0\u8f7d\u5931\u8d25: " + str(e))
        input("\n\u6309\u56de\u8f66\u952e\u9000\u51fa...")
        return

    print("\n\u968f\u673a\u9009\u9898:")
    print("  \u5355\u9009\u9898: " + str(QUESTION_TYPES["single"][1]) + " \u9053")
    print("  \u591a\u9009\u9898: " + str(QUESTION_TYPES["multi"][1]) + " \u9053")
    print("  \u5224\u65ad\u9898: " + str(QUESTION_TYPES["judge"][1]) + " \u9053")
    input("\n\u56de\u8f66\u5f00\u59cb\u7b54\u9898...")

    qs = []
    qs += pick(singles, QUESTION_TYPES["single"][1])
    qs += pick(multis, QUESTION_TYPES["multi"][1])
    qs += pick(judges, QUESTION_TYPES["judge"][1])
    random.shuffle(qs)
    run(qs)


if __name__ == "__main__":
    main()
