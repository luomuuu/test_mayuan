# -*- coding: utf-8 -*-
"""马克思主义基本原理刷题系统 - Web版
运行: python3 quiz_web.py
然后浏览器打开 http://localhost:8080
"""
import os
import re
import json
import random
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8080
QUESTION_TYPES = {
    "single": ("单选题", 40),
    "multi": ("多选题", 20),
    "judge": ("判断题", 20),
}

# ---------- 题库加载 ----------

def load_questions():
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

    def _save(num, question, opts, answer):
        nonlocal singles, multis, judges
        if num is None or not question or answer is None:
            return
        q = {"num": num, "question": question, "options": opts, "answer": answer}
        if answer in ("正确", "错误"):
            judges.append(q)
        elif len(answer) > 1:
            multis.append(q)
        else:
            singles.append(q)

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
            _save(cur_num, cur_q, cur_opts, cur_ans)
            cur_num = int(qm.group(1))
            cur_q = qm.group(2)
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
        elif cur_q:
            cur_q += " " + s

    _save(cur_num, cur_q, cur_opts, cur_ans)
    return singles, multis, judges

# ---------- HTML 页面 ----------

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>马原复习系统</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f0f4f8; min-height:100vh; padding:20px; }
.container { max-width:1100px; margin:0 auto; background:#fff; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,0.08); padding:40px; }
.hidden { display:none !important; }

h1 { text-align:center; color:#1a5fb4; font-size:26px; margin-bottom:32px; }
.btn { display:inline-block; padding:12px 32px; font-size:16px; border:none; border-radius:8px; cursor:pointer; transition:all .2s; }
.btn-primary { background:#1a5fb4; color:#fff; }
.btn-primary:hover { background:#145091; }
.btn-primary:disabled { background:#a0b4cc; cursor:not-allowed; }
.btn-outline { background:#fff; color:#1a5fb4; border:2px solid #1a5fb4; }
.btn-outline:hover { background:#e8f0fa; }
.btn-danger { background:#fff; color:#e74c3c; border:2px solid #e74c3c; }
.btn-sm { padding:6px 16px; font-size:13px; }
.stats { background:#f7f9fc; border-radius:12px; padding:24px; margin:20px 0; line-height:2; font-size:15px; }

/* Quiz layout: two columns */
.quiz-layout { display:flex; gap:20px; min-height:500px; }
.quiz-left { flex:1; min-width:0; }
.quiz-right { width:230px; flex-shrink:0; }

.quiz-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.quiz-header .progress { font-size:16px; font-weight:bold; color:#333; }
.quiz-header .type-badge { background:#1a5fb4; color:#fff; padding:4px 14px; border-radius:20px; font-size:13px; white-space:nowrap; }
.question-text { font-size:17px; line-height:1.8; margin-bottom:20px; color:#222; }
.option { display:block; padding:14px 18px; margin:8px 0; border:2px solid #e0e5ec; border-radius:10px; cursor:pointer; font-size:15px; transition:all .15s; }
.option:hover { border-color:#1a5fb4; background:#f5f8fc; }
.option input { margin-right:10px; transform:scale(1.2); accent-color:#1a5fb4; }
.option.selected { border-color:#1a5fb4; background:#e8f0fa; }
.option.locked { pointer-events:none; opacity:0.7; }
.feedback { font-size:15px; padding:8px 0; min-height:30px; }
.feedback.correct { color:#27ae60; }
.feedback.wrong { color:#e74c3c; }
.nav-buttons { display:flex; justify-content:space-between; margin-top:20px; gap:10px; flex-wrap:wrap; }

/* Answer Card */
.answer-card { background:#f7f9fc; border-radius:12px; padding:16px; position:sticky; top:20px; }
.answer-card h3 { text-align:center; font-size:15px; margin-bottom:12px; color:#333; }
.answer-card-grid { display:grid; grid-template-columns:repeat(8,1fr); gap:4px; }
.answer-card-cell { aspect-ratio:1; display:flex; align-items:center; justify-content:center; border-radius:6px; font-size:12px; font-weight:bold; color:#fff; cursor:pointer; transition:all .15s; border:2px solid transparent; }
.answer-card-cell.unanswered { background:#c0c8d4; }
.answer-card-cell.answered { background:#1a5fb4; }
.answer-card-cell.current { border-color:#1a5fb4; box-shadow:0 0 0 3px rgba(26,95,180,0.3); }
.answer-card-cell:hover { opacity:0.8; transform:scale(1.05); }
.answer-card-info { text-align:center; font-size:13px; margin-top:12px; color:#666; }
.answer-card-legend { display:flex; justify-content:center; gap:12px; font-size:11px; color:#999; margin-top:6px; }

/* Results */
.result { text-align:center; }
.result .score { font-size:48px; font-weight:bold; color:#1a5fb4; margin:20px 0; }
.result .grade { font-size:24px; font-weight:bold; margin:10px 0 30px; }
.result-detail { display:grid; grid-template-columns:1fr 1fr; gap:12px; text-align:left; margin:20px auto; max-width:500px; }
.result-detail div { background:#f7f9fc; padding:12px 16px; border-radius:8px; font-size:15px; }
.result-card-grid { display:inline-grid; grid-template-columns:repeat(8,1fr); gap:4px; margin:20px auto; }
.result-card-cell { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:5px; font-size:10px; font-weight:bold; color:#fff; }
.result-card-cell.correct { background:#27ae60; }
.result-card-cell.wrong { background:#e74c3c; }
.result-card-cell.unanswered { background:#c0c8d4; }

/* History */
.history { margin-top:30px; }
.history table { width:100%; border-collapse:collapse; font-size:14px; }
.history th, .history td { padding:10px 12px; text-align:left; border-bottom:1px solid #e0e5ec; }
.history th { background:#f7f9fc; font-weight:bold; color:#555; }
.history tr:hover { background:#f5f8fc; }
.history .expand-btn { cursor:pointer; color:#1a5fb4; text-decoration:underline; font-size:13px; }
</style>
</head>
<body>
<div class="container">
  <div id="home">
    <h1>马原复习考试系统</h1>
    <div style="text-align:center">
      <button class="btn btn-primary" onclick="loadQuestions()">加载题库</button>
    </div>
    <div id="statsArea" class="stats hidden"></div>
    <div id="historyArea" class="history hidden">
      <h3 style="margin-bottom:16px;color:#555;">📊 历史记录</h3>
      <div id="historyTable"></div>
      <div style="text-align:center;margin-top:12px">
        <button class="btn btn-outline btn-sm" onclick="clearHistory()">清空记录</button>
      </div>
    </div>
    <div id="wrongQuestionsArea" class="history hidden">
      <h3 style="margin-bottom:16px;color:#555;">📝 错题本</h3>
      <div id="wrongQuestionsInfo"></div>
      <div style="text-align:center;margin-top:12px">
        <button id="wrongQuizBtn" class="btn btn-primary" onclick="startWrongQuiz()">练习错题</button>
      </div>
    </div>
    <div style="text-align:center;margin-top:20px">
      <button id="startBtn" class="btn btn-primary hidden" onclick="startQuiz()">开始考试</button>
    </div>
  </div>

  <div id="quiz" class="hidden">
    <div class="quiz-layout">
      <div class="quiz-left">
        <div class="quiz-header">
          <span class="progress" id="progress"></span>
          <span class="type-badge" id="typeBadge"></span>
        </div>
        <div class="question-text" id="questionText"></div>
        <div id="optionsArea"></div>
        <div class="feedback" id="feedback"></div>
        <div class="nav-buttons">
          <button class="btn btn-outline" id="prevBtn" onclick="prevQuestion()">上一题</button>
          <button class="btn btn-outline" id="nextBtn" onclick="nextQuestion()">下一题</button>
          <button class="btn btn-danger" onclick="submitExam()">交卷</button>
        </div>
      </div>
      <div class="quiz-right">
        <div class="answer-card" id="answerCard">
          <h3>📋 答题卡</h3>
          <div class="answer-card-grid" id="answerCardGrid"></div>
          <div class="answer-card-info" id="answerCardInfo"></div>
          <div class="answer-card-legend" id="answerCardLegend">
            <span style="color:#1a5fb4">● 已答</span>
            <span style="color:#c0c8d4">● 未答</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div id="result" class="hidden result">
    <h1>考试结束！</h1>
    <div class="result-detail" id="resultDetail"></div>
    <div class="score" id="scoreText"></div>
    <div class="grade" id="gradeText"></div>
    <div class="result-card-grid" id="resultCardGrid"></div>
    <div style="margin:4px 0;font-size:12px;color:#999;">点击题号查看详情</div>
    <div id="reviewPanel" style="text-align:left;max-width:600px;margin:0 auto;"></div>
    <div style="margin-top:20px">
      <button class="btn btn-primary" onclick="restartQuiz()">再考一次</button>
      <button class="btn btn-outline" onclick="goHome()" style="margin-left:12px">返回首页</button>
    </div>
  </div>
</div>

<script>
let allQuestions = {singles:[], multis:[], judges:[]};
let quizQuestions = [];
let currentIndex = 0;
let submitted = [];
let currentSelection = null;
let examSubmitted = false;
let isWrongQuiz = false;

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

async function loadQuestions() {
  try {
    const resp = await fetch('/api/questions');
    allQuestions = await resp.json();
    document.getElementById('statsArea').innerHTML = `
      <strong>📚 题库加载成功！</strong><br><br>
      单选题：${allQuestions.singles.length} 道<br>
      多选题：${allQuestions.multis.length} 道<br>
      判断题：${allQuestions.judges.length} 道<br>
      总计：${allQuestions.singles.length + allQuestions.multis.length + allQuestions.judges.length} 道<br><br>
      <strong>🎯 本次考试：</strong><br>
      单选题：40 道（1分/题）&nbsp;|&nbsp; 多选题：20 道（2分/题）&nbsp;|&nbsp; 判断题：20 道（1分/题）<br>
      总计：80 道&nbsp;|&nbsp;总分：100 分
    `;
    show('statsArea');
    show('startBtn');
    loadAndShowHistory();
  } catch(e) {
    document.getElementById('statsArea').innerHTML = '<strong style="color:#e74c3c">❌ 加载失败，请检查网络后刷新页面重试</strong>';
    show('statsArea');
  }
}

function shuffle(arr) {
  for (let i = arr.length-1; i>0; i--) {
    const j = Math.floor(Math.random()*(i+1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function pick(arr, n) {
  const a = [...arr];
  shuffle(a);
  return a.slice(0, Math.min(n, a.length));
}

function startQuiz() {
  quizQuestions = [
    ...pick(allQuestions.singles, 40),
    ...pick(allQuestions.multis, 20),
    ...pick(allQuestions.judges, 20)
  ];
  currentIndex = 0;
  submitted = quizQuestions.map(() => null);
  currentSelection = null;
  examSubmitted = false;
  isWrongQuiz = false;
  hide('home');
  show('quiz');
  hide('result');
  renderQuestion();
}

function renderQuestion() {
  const q = quizQuestions[currentIndex];
  const total = quizQuestions.length;

  document.getElementById('progress').textContent = (isWrongQuiz ? '📝 错题练习 · ' : '') + `第 ${currentIndex+1} / ${total} 题`;

  const isJudge = q.answer === '正确' || q.answer === '错误';
  const isMulti = q.answer.length > 1 && !isJudge;
  const typeName = isJudge ? '判断题' : (isMulti ? '多选题' : '单选题');
  const points = isMulti ? 2 : 1;
  document.getElementById('typeBadge').textContent = `${typeName} · ${points}分`;

  document.getElementById('questionText').textContent = q.question;
  document.getElementById('feedback').textContent = '';
  document.getElementById('feedback').className = 'feedback';

  const saved = submitted[currentIndex];
  currentSelection = saved ? saved.answer : null;

  document.getElementById('prevBtn').style.visibility = currentIndex > 0 ? 'visible' : 'hidden';
  const nextBtn = document.getElementById('nextBtn');
  if (nextBtn) {
    nextBtn.textContent = currentIndex < total - 1 ? '下一题' : '已是最后一题';
    nextBtn.style.visibility = currentIndex < total - 1 ? 'visible' : 'hidden';
  }

  const area = document.getElementById('optionsArea');
  area.innerHTML = '';

  const isSubmitted = saved !== null;
  const isLocked = isSubmitted || examSubmitted;

  if (isJudge) {
    ['正确', '错误'].forEach((text, i) => {
      const label = document.createElement('label');
      label.className = 'option' + (currentSelection === text ? ' selected' : '') + (isLocked ? ' locked' : '');
      const radio = document.createElement('input');
      radio.type = 'radio'; radio.name = 'opt'; radio.value = text;
      radio.checked = currentSelection === text;
      radio.disabled = isLocked;
      if (!isLocked) {
        radio.onchange = () => {
          currentSelection = text;
          document.querySelectorAll('#optionsArea .option').forEach(o => o.classList.remove('selected'));
          label.classList.add('selected');
          onOptionSelected();
        };
      }
      label.appendChild(radio);
      label.appendChild(document.createTextNode(`${'AB'[i]}. ${text}`));
      area.appendChild(label);
    });
  } else if (isMulti) {
    const selectedSet = new Set(currentSelection ? currentSelection.split('') : []);
    q.options.forEach(opt => {
      const m = opt.match(/^([A-D])[、．.]\s*(.*)/);
      if (!m) return;
      const letter = m[1], text = m[2];
      const label = document.createElement('label');
      label.className = 'option' + (selectedSet.has(letter) ? ' selected' : '') + (isLocked ? ' locked' : '');
      const cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = letter;
      cb.checked = selectedSet.has(letter);
      cb.disabled = isLocked;
      if (!isLocked) {
        cb.onchange = () => {
          if (cb.checked) selectedSet.add(letter);
          else selectedSet.delete(letter);
          document.querySelectorAll('#optionsArea .option').forEach(o => o.classList.remove('selected'));
          document.querySelectorAll('#optionsArea input:checked').forEach(inp => inp.closest('.option').classList.add('selected'));
        };
      }
      label.appendChild(cb);
      label.appendChild(document.createTextNode(opt));
      area.appendChild(label);
    });
    if (!isLocked) {
      const confirmBtn = document.createElement('button');
      confirmBtn.className = 'btn btn-primary';
      confirmBtn.textContent = '确认答案';
      confirmBtn.style.marginTop = '16px';
      confirmBtn.style.padding = '10px 32px';
      confirmBtn.style.fontSize = '15px';
      confirmBtn.onclick = () => {
        const s = new Set();
        document.querySelectorAll('#optionsArea input:checked').forEach(cb => s.add(cb.value));
        if (s.size === 0) {
          alert('请至少选择一个选项');
          return;
        }
        currentSelection = [...s].sort().join('');
        onOptionSelected();
      };
      area.appendChild(confirmBtn);
    }
  } else {
    q.options.forEach(opt => {
      const m = opt.match(/^([A-D])[、．.]\s*(.*)/);
      if (!m) return;
      const letter = m[1], text = m[2];
      const label = document.createElement('label');
      label.className = 'option' + (currentSelection === letter ? ' selected' : '') + (isLocked ? ' locked' : '');
      const radio = document.createElement('input');
      radio.type = 'radio'; radio.name = 'opt'; radio.value = letter;
      radio.checked = currentSelection === letter;
      radio.disabled = isLocked;
      if (!isLocked) {
        radio.onchange = () => {
          currentSelection = letter;
          document.querySelectorAll('#optionsArea .option').forEach(o => o.classList.remove('selected'));
          label.classList.add('selected');
          onOptionSelected();
        };
      }
      label.appendChild(radio);
      label.appendChild(document.createTextNode(opt));
      area.appendChild(label);
    });
  }

  if (saved) {
    showFeedback();
  }

  renderAnswerCard();
}

function renderAnswerCard() {
  const grid = document.getElementById('answerCardGrid');
  const total = quizQuestions.length;
  grid.innerHTML = '';

  for (let i = 0; i < total; i++) {
    const cell = document.createElement('div');
    cell.className = 'answer-card-cell';
    cell.textContent = i + 1;

    const s = submitted[i];
    if (i === currentIndex) {
      cell.classList.add('current');
      cell.classList.add(s ? 'answered' : 'unanswered');
    } else if (s) {
      cell.classList.add('answered');
    } else {
      cell.classList.add('unanswered');
    }

    cell.onclick = () => {
      if (i !== currentIndex) {
        currentIndex = i;
        currentSelection = submitted[i] ? submitted[i].answer : null;
        renderQuestion();
      }
    };
    grid.appendChild(cell);
  }

  const answered = submitted.filter(s => s !== null).length;
  document.getElementById('answerCardInfo').textContent = `已答：${answered} / ${total}`;
}

function onOptionSelected() {
  if (examSubmitted) return;
  const q = quizQuestions[currentIndex];
  const isJudge = q.answer === '正确' || q.answer === '错误';
  const isMulti = q.answer.length > 1 && !isJudge;

  let userAnswer;
  if (isJudge) {
    const checked = document.querySelector('#optionsArea input:checked');
    userAnswer = checked ? checked.value : null;
  } else if (isMulti) {
    const s = new Set();
    document.querySelectorAll('#optionsArea input:checked').forEach(cb => s.add(cb.value));
    userAnswer = s.size > 0 ? [...s].sort().join('') : null;
  } else {
    const checked = document.querySelector('#optionsArea input:checked');
    userAnswer = checked ? checked.value : null;
  }

  if (!userAnswer) return;

  const isCorrect = check(userAnswer, q.answer);
  submitted[currentIndex] = {
    answer: userAnswer,
    correct: isCorrect
  };

  showFeedback();
  renderAnswerCard();

  if (currentIndex < quizQuestions.length - 1) {
    setTimeout(() => {
      currentIndex++;
      currentSelection = null;
      renderQuestion();
    }, 1200);
  } else {
    setTimeout(() => {
      if (confirm((isWrongQuiz ? '错题练习' : '考试') + '已完成，确认交卷？')) {
        examSubmitted = true;
        showResult();
      }
    }, 1200);
  }
}

function submitCurrentAnswer() {
  if (examSubmitted) return;
  const q = quizQuestions[currentIndex];
  const isJudge = q.answer === '正确' || q.answer === '错误';
  const isMulti = q.answer.length > 1 && !isJudge;

  let userAnswer;
  if (isJudge) {
    const checked = document.querySelector('#optionsArea input:checked');
    userAnswer = checked ? checked.value : null;
  } else if (isMulti) {
    const s = new Set();
    document.querySelectorAll('#optionsArea input:checked').forEach(cb => s.add(cb.value));
    userAnswer = s.size > 0 ? [...s].sort().join('') : null;
  } else {
    const checked = document.querySelector('#optionsArea input:checked');
    userAnswer = checked ? checked.value : null;
  }

  if (!userAnswer) return;

  const isCorrect = check(userAnswer, q.answer);

  submitted[currentIndex] = {
    answer: userAnswer,
    correct: isCorrect
  };

  showFeedback();
  renderAnswerCard();
}

function nextQuestion() {
  if (currentIndex < quizQuestions.length - 1) {
    currentIndex++;
    currentSelection = submitted[currentIndex] ? submitted[currentIndex].answer : null;
    renderQuestion();
  }
}

function check(user, correct) {
  let s1 = user.trim().toUpperCase().replace(/，/g, ',').replace(/\s/g, '').replace(/、/g, ',');
  let s2 = correct.trim().toUpperCase().replace(/，/g, ',').replace(/\s/g, '').replace(/、/g, ',');
  return [...s1.split(',')].sort().join('') === [...s2.split(',')].sort().join('');
}

function showFeedback() {
  const s = submitted[currentIndex];
  if (!s) return;
  const fb = document.getElementById('feedback');
  if (s.correct) {
    fb.textContent = '✓ 回答正确！';
    fb.className = 'feedback correct';
  } else {
    fb.textContent = '✗ 正确答案：' + quizQuestions[currentIndex].answer;
    fb.className = 'feedback wrong';
  }
}

function prevQuestion() {
  if (currentIndex > 0) {
    currentIndex--;
    currentSelection = submitted[currentIndex] ? submitted[currentIndex].answer : null;
    renderQuestion();
  }
}

function submitExam() {
  const answered = submitted.filter(s => s !== null).length;
  const unanswered = quizQuestions.length - answered;
  const label = isWrongQuiz ? '错题练习' : '考试';
  if (confirm(`${label} — 已答 ${answered} 题，未答 ${unanswered} 题。确认交卷？`)) {
    examSubmitted = true;
    showResult();
  }
}

function showResult() {
  hide('quiz');
  show('result');

  const total = quizQuestions.length;

  // Compute correctness at submit time
  let correctCount = 0;
  let earned = 0;
  let maxScore = 0;
  submitted.forEach((s, i) => {
    const q = quizQuestions[i];
    const isMulti = q.answer.length > 1 && q.answer !== '正确' && q.answer !== '错误';
    maxScore += isMulti ? 2 : 1;
    if (!s) return;
    const isCorrect = check(s.answer, q.answer);
    s.correct = isCorrect;
    if (isCorrect) {
      correctCount++;
      earned += isMulti ? 2 : 1;
    }
  });
  const accuracy = total > 0 ? (correctCount / total * 100) : 0;

  document.getElementById('resultDetail').innerHTML = `
    <div>📝 总题数<br><strong>${total} 题</strong></div>
    <div>✅ 正确<br><strong>${correctCount} 题</strong></div>
    <div>❌ 错误<br><strong>${total - correctCount} 题</strong></div>
    <div>📊 正确率<br><strong>${accuracy.toFixed(1)}%</strong></div>
  `;
  document.getElementById('scoreText').textContent = `${earned} / ${maxScore} 分`;

  let grade, color;
  if (accuracy >= 80) { grade = '🎉 优秀！继续保持！'; color = '#27ae60'; }
  else if (accuracy >= 60) { grade = '👍 良好！还需努力！'; color = '#f39c12'; }
  else { grade = '💪 加油！多做练习！'; color = '#e74c3c'; }
  document.getElementById('gradeText').textContent = grade;
  document.getElementById('gradeText').style.color = color;

  renderResultAnswerCard();
  saveHistory(earned, correctCount, total - correctCount, accuracy, maxScore);
}

function renderResultAnswerCard() {
  const grid = document.getElementById('resultCardGrid');
  grid.innerHTML = '';
  for (let i = 0; i < quizQuestions.length; i++) {
    const cell = document.createElement('div');
    cell.className = 'result-card-cell';
    cell.textContent = i + 1;
    cell.style.cursor = 'pointer';
    const s = submitted[i];
    if (!s) {
      cell.classList.add('unanswered');
    } else if (s.correct) {
      cell.classList.add('correct');
    } else {
      cell.classList.add('wrong');
    }
    cell.onclick = () => reviewQuestion(i);
    grid.appendChild(cell);
  }
}

function reviewQuestion(index) {
  const q = quizQuestions[index];
  const s = submitted[index];
  if (!s) return;

  const isJudge = q.answer === '正确' || q.answer === '错误';
  const isCorrect = s.correct;
  const typeName = isJudge ? '判断题' : (q.answer.length > 1 ? '多选题' : '单选题');

  let optionsHtml = '';
  if (isJudge) {
    optionsHtml = `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${s.answer==='正确'?'background:#ffeaea;':'background:#eaf7ea;'}">A. 正确</div>`;
    optionsHtml += `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${s.answer==='错误'?'background:#ffeaea;':'background:#eaf7ea;'}">B. 错误</div>`;
  } else {
    q.options.forEach(opt => {
      let bg = '';
      if (isCorrect) {
        bg = 'background:#eaf7ea;';
      } else {
        const letter = (opt.match(/^([A-D])/) || [])[1];
        const userHas = s.answer.includes(letter);
        const correctHas = q.answer.includes(letter);
        if (correctHas) bg = 'background:#eaf7ea;';
        else if (userHas) bg = 'background:#ffeaea;';
      }
      optionsHtml += `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${bg}">${opt}</div>`;
    });
  }

  const panel = document.getElementById('reviewPanel');
  panel.innerHTML = `
    <div style="background:#f7f9fc;border-radius:12px;padding:20px;margin-top:16px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-weight:bold;font-size:15px;color:#333;">第 ${index+1} 题 · ${typeName}</span>
        <span style="font-size:14px;font-weight:bold;color:${isCorrect?'#27ae60':'#e74c3c'}">${isCorrect?'✓ 正确':'✗ 错误'}</span>
      </div>
      <div style="font-size:16px;line-height:1.8;margin-bottom:12px;color:#222;">${q.question}</div>
      ${optionsHtml}
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e0e5ec;font-size:14px;">
        <span style="color:#666;">你的答案：</span><span style="font-weight:bold;color:${isCorrect?'#27ae60':'#e74c3c'}">${s.answer || '(未作答)'}</span>
        ${!isCorrect ? `<span style="margin-left:16px;color:#666;">正确答案：</span><span style="font-weight:bold;color:#27ae60">${q.answer}</span>` : ''}
      </div>
    </div>`;
  panel.scrollIntoView({behavior:'smooth',block:'center'});
}

function saveHistory(score, correctCount, wrongCount, accuracy, totalScore) {
  try {
    const record = {
      date: new Date().toLocaleString('zh-CN'),
      score: score,
      total: totalScore || 100,
      accuracy: accuracy,
      correctCount: correctCount,
      wrongCount: wrongCount,
      unansweredCount: quizQuestions.length - correctCount - wrongCount,
      details: quizQuestions.map((q, i) => {
        const s = submitted[i];
        return {
          qType: q.answer === '正确' || q.answer === '错误' ? 'judge' : (q.answer.length > 1 ? 'multi' : 'single'),
          question: q.question,
          options: q.options,
          answer: q.answer,
          userAnswer: s ? s.answer : '',
          correct: s ? s.correct : false
        };
      })
    };
    let history = [];
    try {
      const raw = localStorage.getItem('quiz_history');
      if (raw) history = JSON.parse(raw);
    } catch(e) { history = []; }
    history.unshift(record);
    if (history.length > 50) history = history.slice(0, 50);
    localStorage.setItem('quiz_history', JSON.stringify(history));
  } catch(e) {}
}

function loadAndShowHistory() {
  const historyArea = document.getElementById('historyArea');
  try {
    const raw = localStorage.getItem('quiz_history');
    if (!raw) { historyArea.classList.add('hidden'); loadWrongQuestions(); return; }
    const history = JSON.parse(raw);
    if (history.length === 0) { historyArea.classList.add('hidden'); loadWrongQuestions(); return; }

    historyArea.classList.remove('hidden');
    let html = '<table><thead><tr><th>日期</th><th>得分</th><th>正确率</th><th>详情</th></tr></thead><tbody>';
    const display = history.slice(0, 20);
    for (let i = 0; i < display.length; i++) {
      const r = display[i];
      html += `<tr>
        <td>${r.date}</td>
        <td>${r.score} / ${r.total}</td>
        <td>${r.accuracy.toFixed(1)}%</td>
        <td><span class="expand-btn" onclick="showHistoryDetail(${i})">查看答题卡</span></td>
      </tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('historyTable').innerHTML = html;
    loadWrongQuestions();
  } catch(e) {
    localStorage.removeItem('quiz_history');
    historyArea.classList.add('hidden');
    loadWrongQuestions();
  }
}

function showHistoryDetail(index) {
  try {
    const raw = localStorage.getItem('quiz_history');
    const history = JSON.parse(raw);
    const record = history[index];
    if (!record || !record.details) return;

    let html = '<div style="display:inline-grid;grid-template-columns:repeat(8,1fr);gap:4px;margin:8px 0">';
    record.details.forEach((d, i) => {
      let cls = 'unanswered';
      if (!d.userAnswer) cls = 'unanswered';
      else if (d.correct) cls = 'correct';
      else cls = 'wrong';
      html += `<div class="result-card-cell ${cls}" style="cursor:pointer" onclick="reviewHistoryQuestion(${index},${i})">${i + 1}</div>`;
    });
    html += '</div>';
    html += '<div id="historyReviewPanel" style="text-align:left;max-width:500px;margin:0 auto;"></div>';
    html += '<button class="btn btn-outline btn-sm" onclick="loadAndShowHistory()" style="margin-top:8px;">收起</button>';

    document.getElementById('historyTable').innerHTML = html;
  } catch(e) {}
}

function reviewHistoryQuestion(historyIndex, questionIndex) {
  try {
    const raw = localStorage.getItem('quiz_history');
    const history = JSON.parse(raw);
    const d = history[historyIndex].details[questionIndex];
    if (!d) return;

    const isJudge = d.qType === 'judge';
    const isCorrect = d.correct;

    let optionsHtml = '';
    if (isJudge) {
      optionsHtml = `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${d.userAnswer==='正确'?'background:#ffeaea;':'background:#eaf7ea;'}">A. 正确</div>`;
      optionsHtml += `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${d.userAnswer==='错误'?'background:#ffeaea;':'background:#eaf7ea;'}">B. 错误</div>`;
    } else if (d.options) {
      d.options.forEach(opt => {
        let bg = '';
        if (isCorrect) {
          bg = 'background:#eaf7ea;';
        } else {
          const letter = (opt.match(/^([A-D])/) || [])[1];
          const userHas = d.userAnswer.includes(letter);
          const correctHas = d.answer.includes(letter);
          if (correctHas) bg = 'background:#eaf7ea;';
          else if (userHas) bg = 'background:#ffeaea;';
        }
        optionsHtml += `<div style="margin:4px 0;padding:6px 10px;border-radius:6px;${bg}">${opt}</div>`;
      });
    }

    const panel = document.getElementById('historyReviewPanel');
    panel.innerHTML = `
      <div style="background:#f7f9fc;border-radius:12px;padding:20px;margin-top:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <span style="font-weight:bold;font-size:15px;color:#333;">第 ${questionIndex+1} 题 · ${isJudge?'判断题':(d.qType==='multi'?'多选题':'单选题')}</span>
          <span style="font-size:14px;font-weight:bold;color:${isCorrect?'#27ae60':'#e74c3c'}">${isCorrect?'✓ 正确':'✗ 错误'}</span>
        </div>
        <div style="font-size:16px;line-height:1.8;margin-bottom:12px;color:#222;">${d.question}</div>
        ${optionsHtml}
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e0e5ec;font-size:14px;">
          <span style="color:#666;">你的答案：</span><span style="font-weight:bold;color:${isCorrect?'#27ae60':'#e74c3c'}">${d.userAnswer || '(未作答)'}</span>
          ${!isCorrect ? `<span style="margin-left:16px;color:#666;">正确答案：</span><span style="font-weight:bold;color:#27ae60">${d.answer}</span>` : ''}
        </div>
      </div>`;
    panel.scrollIntoView({behavior:'smooth',block:'center'});
  } catch(e) {}
}

function loadWrongQuestions() {
  const area = document.getElementById('wrongQuestionsArea');
  area.classList.add('hidden');
  try {
    const raw = localStorage.getItem('quiz_history');
    if (!raw) return;
    const history = JSON.parse(raw);
    
    const seen = new Set();
    const wrongList = [];
    history.forEach(record => {
      if (!record.details) return;
      record.details.forEach(d => {
        if (!d.correct && d.userAnswer && !seen.has(d.question)) {
          seen.add(d.question);
          wrongList.push(d);
        }
      });
    });

    if (wrongList.length === 0) return;

    area.classList.remove('hidden');
    document.getElementById('wrongQuestionsInfo').innerHTML = `
      <p style="color:#666;font-size:14px;">共 <strong style="color:#e74c3c">${wrongList.length}</strong> 道错题（去重后），来自 ${history.length} 次考试记录</p>
    `;
    document.getElementById('wrongQuizBtn').onclick = () => startWrongQuiz(wrongList);
  } catch(e) {}
}

let wrongQuestionsList = [];
function startWrongQuiz(wrongList) {
  if (wrongList) {
    wrongQuestionsList = wrongList;
  }
  if (wrongQuestionsList.length === 0) return;

  quizQuestions = wrongQuestionsList.map((d, idx) => ({
    num: idx + 1,
    question: d.question,
    options: d.options || [],
    answer: d.answer
  }));

  currentIndex = 0;
  submitted = quizQuestions.map(() => null);
  currentSelection = null;
  examSubmitted = false;
  isWrongQuiz = true;
  hide('home');
  show('quiz');
  hide('result');
  renderQuestion();
}

function clearHistory() {
  if (confirm('确认清空所有历史记录？此操作不可恢复。')) {
    localStorage.removeItem('quiz_history');
    document.getElementById('historyArea').classList.add('hidden');
    document.getElementById('wrongQuestionsArea').classList.add('hidden');
    wrongQuestionsList = [];
  }
}

function restartQuiz() {
  hide('result');
  isWrongQuiz = false;
  startQuiz();
}

function goHome() {
  if (!examSubmitted && submitted.some(s => s !== null)) {
    if (!confirm('有未完成的答题，确定退出吗？')) return;
  }
  hide('quiz');
  hide('result');
  show('home');
  examSubmitted = false;
  isWrongQuiz = false;
  loadAndShowHistory();
}
</script>
</body>
</html>"""

# ---------- HTTP Server ----------

class QuizHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/questions':
            singles, multis, judges = load_questions()
            data = {
                "singles": singles,
                "multis": multis,
                "judges": judges,
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def main():
    server = HTTPServer(('localhost', PORT), QuizHandler)
    url = f'http://localhost:{PORT}'
    print(f'马原刷题系统已启动: {url}')
    print('在浏览器中打开上方地址，或等待自动打开...')
    print('按 Ctrl+C 退出')
    try:
        webbrowser.open(url)
    except:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已退出')
        server.server_close()

if __name__ == '__main__':
    main()
