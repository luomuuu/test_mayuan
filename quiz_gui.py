# -*- coding: utf-8 -*-
import os
import re
import random
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

QUESTION_TYPES = {
    "single": ("单选题", 40),
    "multi": ("多选题", 20),
    "judge": ("判断题", 20),
}


def load_questions() -> tuple:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    txt_path = os.path.join(script_dir, "马克思主义基本原理题库.txt")
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    singles, multis, judges = [], [], []
    cur_num, cur_q, cur_opts, cur_ans = None, None, [], None
    cur_section = None

    q_num_re = re.compile(r"^(\d+)\.\s+(.*)")
    ans_re = re.compile(r"^答案[：:]\s*(.+)$")
    opt_re = re.compile(r"^([A-D])[、．.]\s*(.*)")
    section_re = re.compile(r"^[一二三四五六七八九十]+\.(.+)")

    for line in lines:
        s = line.strip()
        if not s:
            continue

        section_m = section_re.match(s)
        if section_m:
            cur_section = section_m.group(1)
            continue

        qm = q_num_re.match(s)
        if qm:
            _save(cur_num, cur_q, cur_opts, cur_ans, singles, multis, judges)
            cur_num = int(qm.group(1))
            cur_q = qm.group(2).rstrip("()（）")
            cur_opts, cur_ans = [], None
            continue

        am = ans_re.match(s)
        if am:
            cur_ans = am.group(1).strip()
            continue

        if s.startswith("解析"):
            continue

        om = opt_re.match(s)
        if om and cur_section == "选择题":
            cur_opts.append(s)
        elif cur_q and cur_section == "选择题":
            cur_q += " " + s

    _save(cur_num, cur_q, cur_opts, cur_ans, singles, multis, judges)
    return singles, multis, judges


def _save(num, question, opts, answer, singles, multis, judges):
    if num is None or not question or answer is None:
        return
    q = {"num": num, "question": question, "options": opts, "answer": answer}
    if answer in ("正确", "错误"):
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
    if "," in s1 or "," in s2:
        return "".join(sorted(s1.split(","))) == "".join(sorted(s2.split(",")))
    else:
        return "".join(sorted(s1)) == "".join(sorted(s2))


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("马原复习系统")
        self.geometry("900x650")
        self.resizable(False, False)
        
        self.singles = []
        self.multis = []
        self.judges = []
        self.questions = []
        self.current_index = 0
        self.correct_count = 0
        self.submitted_answers = []
        
        self._setup_styles()
        self.create_main_frame()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Large.TButton", font=("", 14), padding=10)
        style.configure("Exit.TButton", font=("", 12), padding=5, foreground="#e74c3c")
        style.configure("Quiz.TRadiobutton", font=("", 12))
        style.configure("Quiz.TCheckbutton", font=("", 12))

    def create_main_frame(self):
        self.main_frame = ttk.Frame(self, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            self.main_frame, 
            text="马原复习考试系统",
            font=("", 22, "bold"),
            foreground="#1a5fb4"
        )
        title_label.pack(pady=(0, 40))
        
        load_btn = ttk.Button(
            self.main_frame,
            text="加载题库",
            command=self.load_and_show_stats,
            style="Large.TButton"
        )
        load_btn.pack(pady=10)
        
        self.stats_frame = ttk.Frame(self.main_frame)
        
        self.start_btn = ttk.Button(
            self.main_frame,
            text="开始考试",
            command=self.start_quiz,
            state=tk.DISABLED,
            style="Large.TButton"
        )
        self.start_btn.pack(pady=(30, 0))
        
        style = ttk.Style()
        style.configure("Large.TButton", font=("", 14), padding=10)
        style.configure("Exit.TButton", font=("", 12), padding=5, foreground="#e74c3c")

    def load_and_show_stats(self):
        try:
            self.singles, self.multis, self.judges = load_questions()
            
            for widget in self.stats_frame.winfo_children():
                widget.destroy()
            
            stats_text = f"""
题库加载成功！

📚 题目统计：
  单选题：{len(self.singles)} 道
  多选题：{len(self.multis)} 道
  判断题：{len(self.judges)} 道
  总计：{len(self.singles) + len(self.multis) + len(self.judges)} 道

🎯 本次考试：
  单选题：{QUESTION_TYPES['single'][1]} 道
  多选题：{QUESTION_TYPES['multi'][1]} 道
  判断题：{QUESTION_TYPES['judge'][1]} 道
  总计：{QUESTION_TYPES['single'][1] + QUESTION_TYPES['multi'][1] + QUESTION_TYPES['judge'][1]} 道
            """
            
            stats_label = ttk.Label(
                self.stats_frame,
                text=stats_text,
                font=("", 12),
                justify=tk.LEFT
            )
            stats_label.pack(pady=20)
            self.stats_frame.pack()
            
            self.start_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("加载失败", f"加载题库失败：{str(e)}")

    def start_quiz(self):
        self.questions = []
        self.questions += pick(self.singles, QUESTION_TYPES["single"][1])
        self.questions += pick(self.multis, QUESTION_TYPES["multi"][1])
        self.questions += pick(self.judges, QUESTION_TYPES["judge"][1])
        
        self.current_index = 0
        self.correct_count = 0
        self.submitted_answers = [None] * len(self.questions)
        
        self.main_frame.pack_forget()
        self.create_quiz_frame()
        self.show_question()

    def create_quiz_frame(self):
        self.quiz_frame = ttk.Frame(self, padding="20")
        self.quiz_frame.pack(fill=tk.BOTH, expand=True)
        
        top_bar = ttk.Frame(self.quiz_frame)
        top_bar.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(
            top_bar,
            text="",
            font=("", 14, "bold")
        )
        self.progress_label.pack(side=tk.LEFT)
        
        right_frame = ttk.Frame(top_bar)
        right_frame.pack(side=tk.RIGHT)
        
        self.type_label = ttk.Label(
            right_frame,
            text="",
            font=("", 12),
            foreground="#1a5fb4"
        )
        self.type_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.exit_btn = ttk.Button(
            right_frame,
            text="退出",
            command=self.confirm_exit,
            style="Exit.TButton"
        )
        self.exit_btn.pack(side=tk.RIGHT)
        
        self.question_label = ttk.Label(
            self.quiz_frame,
            text="",
            font=("", 13),
            wraplength=820,
            justify=tk.LEFT
        )
        self.question_label.pack(fill=tk.X, pady=(0, 20))
        
        self.options_frame = ttk.Frame(self.quiz_frame)
        self.options_frame.pack(fill=tk.BOTH, expand=True)
        
        bottom_bar = ttk.Frame(self.quiz_frame)
        bottom_bar.pack(fill=tk.X, pady=(20, 0))
        
        self.feedback_label = ttk.Label(
            bottom_bar,
            text="",
            font=("", 12)
        )
        self.feedback_label.pack(side=tk.LEFT, padx=(0, 20))
        
        nav_frame = ttk.Frame(bottom_bar)
        nav_frame.pack(side=tk.RIGHT)
        
        self.prev_btn = ttk.Button(
            nav_frame,
            text="上一题",
            command=self.go_to_previous,
            style="Large.TButton"
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        self.submit_btn = ttk.Button(
            nav_frame,
            text="提交",
            command=self.submit_answer,
            style="Large.TButton"
        )
        self.submit_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = ttk.Button(
            nav_frame,
            text="下一题",
            command=self.go_to_next,
            style="Large.TButton"
        )
        self.next_btn.pack(side=tk.LEFT, padx=10)

    def show_question(self):
        q = self.questions[self.current_index]
        total = len(self.questions)
        
        self.progress_label.config(text=f"第 {self.current_index + 1} / {total} 题")
        
        if q["answer"] in ("正确", "错误"):
            tname = "判断题"
        elif len(q["answer"]) > 1:
            tname = "多选题"
        else:
            tname = "单选题"
        
        self.type_label.config(text=tname)
        self.question_label.config(text=q["question"])
        
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(text="下一题" if self.current_index < total - 1 else "提交考试")
        self.next_btn.config(state=tk.NORMAL)
        
        self.submit_btn.config(state=tk.DISABLED)
        self.feedback_label.config(text="")
        
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        self.var = tk.StringVar()
        self.check_vars = []
        
        is_submitted = self.submitted_answers[self.current_index] is not None
        if is_submitted:
            saved_answer = self.submitted_answers[self.current_index]["answer"]
        else:
            saved_answer = None
        
        if tname == "判断题":
            options = ["A. 正确", "B. 错误"]
            value_map = {"A": "正确", "B": "错误"}
            reverse_map = {"正确": "A", "错误": "B"}
            for opt in options:
                rb = ttk.Radiobutton(
                    self.options_frame,
                    text=opt,
                    variable=self.var,
                    value=opt[0],
                    command=self.on_select,
                    style="Quiz.TRadiobutton"
                )
                rb.pack(anchor=tk.W, pady=5)
            self.judge_value_map = value_map
            if is_submitted and saved_answer in reverse_map:
                self.var.set(reverse_map[saved_answer])
                self.submit_btn.config(state=tk.DISABLED)
        elif tname == "多选题":
            for opt in q["options"]:
                cb_var = tk.BooleanVar()
                self.check_vars.append((opt[0], cb_var))
                cb = ttk.Checkbutton(
                    self.options_frame,
                    text=opt,
                    variable=cb_var,
                    command=self.on_select_multi,
                    style="Quiz.TCheckbutton"
                )
                cb.pack(anchor=tk.W, pady=5)
            if is_submitted and saved_answer:
                for k, v in self.check_vars:
                    v.set(k in saved_answer)
                self.submit_btn.config(state=tk.DISABLED)
        else:
            for opt in q["options"]:
                rb = ttk.Radiobutton(
                    self.options_frame,
                    text=opt,
                    variable=self.var,
                    value=opt[0],
                    command=self.on_select,
                    style="Quiz.TRadiobutton"
                )
                rb.pack(anchor=tk.W, pady=5)
            if is_submitted and saved_answer:
                self.var.set(saved_answer)
                self.submit_btn.config(state=tk.DISABLED)
        
        if is_submitted:
            self.show_feedback(self.current_index)
    
    def show_feedback(self, index):
        q = self.questions[index]
        if index < len(self.submitted_answers):
            user_ans = self.submitted_answers[index]["answer"]
            is_correct = self.submitted_answers[index]["correct"]
            if is_correct:
                self.feedback_label.config(text="✓ 回答正确！", foreground="green")
            else:
                self.feedback_label.config(text=f"✗ 正确答案：{q['answer']}", foreground="red")

    def on_select(self):
        if self.var.get():
            self.submit_btn.config(state=tk.NORMAL)

    def on_select_multi(self):
        selected = any(v.get() for _, v in self.check_vars)
        self.submit_btn.config(state=tk.NORMAL if selected else tk.DISABLED)

    def submit_answer(self):
        q = self.questions[self.current_index]
        
        if q["answer"] in ("正确", "错误"):
            user_ans = self.judge_value_map.get(self.var.get(), "")
        elif len(q["answer"]) == 1:
            user_ans = self.var.get()
        else:
            user_ans = "".join([k for k, v in self.check_vars if v.get()])
        
        is_correct = check(user_ans, q["answer"])
        
        old_submitted = self.submitted_answers[self.current_index]
        if old_submitted is not None and old_submitted["correct"]:
            self.correct_count -= 1
        
        self.submitted_answers[self.current_index] = {
            "answer": user_ans,
            "correct": is_correct
        }
        
        if is_correct:
            self.correct_count += 1
        
        self.show_feedback(self.current_index)
        self.submit_btn.config(state=tk.DISABLED)

    def go_to_next(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.show_question()
        else:
            self.show_result()

    def go_to_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def confirm_exit(self):
        submitted_count = sum(1 for ans in self.submitted_answers if ans is not None)
        if submitted_count > 0:
            result = messagebox.askyesno(
                "确认退出",
                f"您已经完成了 {submitted_count} 道题的作答，确定要退出吗？\n退出后答题进度将丢失。"
            )
        else:
            result = messagebox.askyesno(
                "确认退出",
                "确定要退出答题吗？退出后答题进度将丢失。"
            )
        
        if result:
            self.quiz_frame.pack_forget()
            self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_result(self):
        self.quiz_frame.pack_forget()
        
        self.result_frame = ttk.Frame(self, padding="40")
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            self.result_frame,
            text="考试结束！",
            font=("", 24, "bold"),
            foreground="#1a5fb4"
        )
        title_label.pack(pady=(0, 30))
        
        total = len(self.questions)
        accuracy = self.correct_count / total * 100
        
        result_text = f"""
📊 考试成绩：

总分：{total} 题
正确：{self.correct_count} 题
错误：{total - self.correct_count} 题
正确率：{accuracy:.1f}%
        """
        
        result_label = ttk.Label(
            self.result_frame,
            text=result_text,
            font=("", 16),
            justify=tk.LEFT
        )
        result_label.pack(pady=20)
        
        if accuracy >= 80:
            grade = "🎉 优秀！继续保持！"
            color = "#2ecc71"
        elif accuracy >= 60:
            grade = "👍 良好！还需努力！"
            color = "#f39c12"
        else:
            grade = "💪 加油！多做练习！"
            color = "#e74c3c"
        
        grade_label = ttk.Label(
            self.result_frame,
            text=grade,
            font=("", 18, "bold"),
            foreground=color
        )
        grade_label.pack(pady=20)
        
        button_frame = ttk.Frame(self.result_frame)
        button_frame.pack(pady=(30, 0))
        
        retry_btn = ttk.Button(
            button_frame,
            text="再考一次",
            command=self.restart,
            style="Large.TButton"
        )
        retry_btn.pack(side=tk.LEFT, padx=20)
        
        home_btn = ttk.Button(
            button_frame,
            text="返回首页",
            command=self.go_home,
            style="Large.TButton"
        )
        home_btn.pack(side=tk.RIGHT, padx=20)

    def restart(self):
        self.result_frame.pack_forget()
        self.start_quiz()

    def go_home(self):
        self.result_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    try:
        app = QuizApp()
        app.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("程序异常", f"发生未预期的错误：\n{traceback.format_exc()}")
