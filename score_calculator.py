import re
import os
from datetime import datetime

# --- Configuration ---
ANSWER_KEY_PATH = "answer key.md"
ATTEMPTS_PATH = "attempts.md"
OUTPUT_HTML_PATH = "final_scorecard.html"

SCORING = {
    "right": 4,
    "wrong": -1,
    "skip": 0,
    "bonus": 4
}

def parse_answer_key(file_path):
    """
    Parses the answer key markdown.
    Detects subjects, emojis, and question ranges from headers.
    Returns: (subjects_config, answer_map)
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return [], {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern: # [emoji] **NAME (START-END)**
    subject_matches = re.finditer(r"#\s*(\S+)\s*\*\*([^*]+?)\s*\((\d+)[-–](\d+)\)\*\*", content)
    subjects = []
    for m in subject_matches:
        subjects.append({
            "name": m.group(2).strip().title(),
            "emoji": m.group(1),
            "range": (int(m.group(3)), int(m.group(4)))
        })

    # 2. Extract Answers
    # Pattern: 1-D, 22-A, 180-Bonus, 5-A/B
    answers = {}
    ans_matches = re.finditer(r"(\d+)-([A-D/]+|Bonus)", content)
    for m in ans_matches:
        q_num = int(m.group(1))
        ans_val = m.group(2)
        if '/' in ans_val:
            answers[q_num] = ans_val.split('/')
        else:
            answers[q_num] = ans_val
            
    return subjects, answers

def parse_attempts(file_path, default_str=""):
    """
    Reads attempts from external file or uses default string.
    """
    content = default_str
    if os.path.exists(file_path):
        print(f"[i] Reading attempts from {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        print("[w] attempts.md not found, using default data.")
            
    marked = {}
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        # Only process lines matching "A-1,2,3" or "A - 1,2,3" (strict start)
        match = re.match(r"^([A-D])\s*-\s*(.+)$", line, re.IGNORECASE)
        if not match: continue
        
        option = match.group(1).upper()
        nums_part = match.group(2)
        
        # Numbers can be comma separated and include ranges like 134-139
        parts = nums_part.split(',')
        for part in parts:
            part = part.strip()
            if not part: continue
            
            if '-' in part and part.count('-') == 1:
                try:
                    start, end = part.split('-')
                    for q_num in range(int(start), int(end) + 1):
                        marked[q_num] = option
                except ValueError: pass
            else:
                try:
                    marked[int(part)] = option
                except ValueError: pass
    return marked

def generate_html(data, total_metrics):
    """
    Generates a premium, wow-factor HTML scorecard.
    """
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEET Scorecard | Medjeex</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #4F46E5;
            --primary-light: #818CF8;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
            --slate-50: #F8FAFC;
            --slate-100: #F1F5F9;
            --slate-200: #E2E8F0;
            --slate-700: #334155;
            --slate-800: #1E293B;
            --slate-900: #0F172A;
            --glass: rgba(255, 255, 255, 0.7);
            --glass-border: rgba(255, 255, 255, 0.3);
        }}

        body {{
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
            color: var(--slate-900);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            animation: fadeInDown 0.8s ease-out;
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(to right, var(--primary), #8B5CF6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .header p {{
            color: var(--slate-700);
            font-size: 1.1rem;
            margin-top: 10px;
        }}

        /* Summary Dashboard */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .card {{
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.07);
            transition: transform 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
        }}

        .score-card {{
            grid-column: span 2;
            background: linear-gradient(135deg, var(--primary) 0%, #6366F1 100%);
            color: white;
        }}

        .stat-label {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
        }}

        .stat-sub {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        /* Subject Section */
        .subject-section {{
            margin-bottom: 30px;
        }}

        .subject-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }}

        .subject-header h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
        }}

        .subject-grid {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }}

        @media (max-width: 768px) {{
            .subject-grid {{ grid-template-columns: 1fr; }}
            .score-card {{ grid-column: span 1; }}
        }}

        .chart-box {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .details-box {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .q-group-label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--slate-700);
            text-transform: uppercase;
        }}

        .tag-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .tag {{
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
            border: 1px solid transparent;
        }}

        .tag-correct {{ background: #D1FAE5; color: #065F46; border-color: #A7F3D0; }}
        .tag-wrong {{ background: #FEE2E2; color: #991B1B; border-color: #FECACA; }}
        .tag-skip {{ background: #F1F5F9; color: #475569; border-color: #E2E8F0; }}
        .tag-bonus {{ background: #FEF3C7; color: #92400E; border-color: #FDE68A; }}

        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .footer {{
            text-align: center;
            margin-top: 60px;
            padding-bottom: 40px;
            color: var(--slate-700);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NEET performance Scorecard</h1>
            <p>Analysis of your attempt generated on {date}</p>
        </div>

        <div class="summary-grid">
            <div class="card score-card">
                <div class="stat-label">Final Score</div>
                <div class="stat-value">{total_score} / 720</div>
                <div class="stat-sub">Based on +4 / -1 marking scheme</div>
            </div>
            <div class="card" style="border-left: 6px solid var(--success)">
                <div class="stat-label" style="color: var(--success)">Correct</div>
                <div class="stat-value" style="color: var(--success)">{total_right}</div>
            </div>
            <div class="card" style="border-left: 6px solid var(--danger)">
                <div class="stat-label" style="color: var(--danger)">Wrong</div>
                <div class="stat-value" style="color: var(--danger)">{total_wrong}</div>
            </div>
            <div class="card" style="border-left: 6px solid var(--warning)">
                <div class="stat-label" style="color: var(--warning)">Unattempted</div>
                <div class="stat-value" style="color: var(--warning)">{total_skip}</div>
            </div>
        </div>

        {subject_cards}

        <div class="footer">
            <p>&copy; 2024 Medjeex Exam Studio. All Rights Reserved.</p>
        </div>
    </div>

    <script>
        {chart_scripts}
    </script>
</body>
</html>
"""
    
    subject_card_template = """
    <div class="subject-section">
        <div class="subject-header">
            <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.8rem;">{emoji}</span>
                    <h2>{name} <span style="font-size: 0.9rem; font-weight: 400; color: var(--slate-700);">(Q{start}–{end})</span></h2>
                </div>
                <div style="font-size: 1.4rem; font-weight: 700; color: var(--primary);">
                    {score} / {max_score} <span style="font-size: 0.8rem; font-weight: 400; color: var(--slate-700);">Marks</span>
                </div>
            </div>
        </div>
        <div class="card subject-grid">
            <div class="chart-box">
                <canvas id="chart-{id}" width="180" height="180"></canvas>
            </div>
            <div class="details-box">
                <div style="display: flex; gap: 20px; margin-bottom: 5px;">
                    <div><span style="color: var(--success); font-weight: 700;">{right_count}</span> Correct</div>
                    <div><span style="color: var(--danger); font-weight: 700;">{wrong_count}</span> Wrong</div>
                    <div><span style="color: var(--warning); font-weight: 700;">{skip_count}</span> Skipped</div>
                </div>

                <div>
                   <div class="q-group-label" style="color: var(--success)">Correct Questions</div>
                   <div class="tag-list">{right_tags}</div>
                </div>
                
                <div>
                   <div class="q-group-label" style="color: var(--danger)">Wrong (Marked &rarr; Correct)</div>
                   <div class="tag-list">{wrong_tags}</div>
                </div>
                
                <div>
                   <div class="q-group-label" style="color: var(--slate-700)">Skipped (Correct Key)</div>
                   <div class="tag-list">{skip_tags}</div>
                </div>
            </div>
        </div>
    </div>
    """

    subject_cards_html = ""
    chart_scripts = ""
    
    for i, sub in enumerate(data):
        sub_id = f"sub_{i}"
        
        # 1. Right Tags
        right_items = []
        for q in sub['right_list']:
            ans = total_metrics['ans_map'].get(q)
            display_ans = "/".join(ans) if isinstance(ans, list) else ans
            right_items.append(f'<span class="tag tag-correct">{q} ({display_ans})</span>')
        right_tags = "".join(right_items) or '<span style="font-size:0.8rem; color: #999">None</span>'

        # 2. Wrong Tags
        wrong_items_list = []
        for w in sub['wrong_list']:
            display_ans = "/".join(w[2]) if isinstance(w[2], list) else w[2]
            wrong_items_list.append(f'<span class="tag tag-wrong" title="You marked {w[1]}, correct was {display_ans}">{w[0]} ({w[1]}&rarr;{display_ans})</span>')
        wrong_tags = "".join(wrong_items_list) or '<span style="font-size:0.8rem; color: #999">None</span>'
        
        # 3. Skip Tags
        skip_tags_list = []
        for q in sub['skip_list']:
            ans = total_metrics['ans_map'].get(q)
            display_ans = "/".join(ans) if isinstance(ans, list) else ans
            skip_tags_list.append(f'<span class="tag tag-skip">{q} ({display_ans})</span>')
        skip_tags = "".join(skip_tags_list) or '<span style="font-size:0.8rem; color: #999">None</span>'
        
        subject_cards_html += subject_card_template.format(
            id=sub_id,
            emoji=sub['emoji'],
            name=sub['name'],
            start=sub['range'][0],
            end=sub['range'][1],
            right_count=len(sub['right_list']),
            wrong_count=len(sub['wrong_list']),
            skip_count=len(sub['skip_list']),
            score=sub['score'],
            max_score=(sub['range'][1] - sub['range'][0] + 1) * 4,
            right_tags=right_tags,
            wrong_tags=wrong_tags,
            skip_tags=skip_tags
        )
        
        # Add JS for chart
        chart_scripts += f"""
        new Chart(document.getElementById('chart-{sub_id}'), {{
            type: 'doughnut',
            data: {{
                labels: ['Correct', 'Wrong', 'Skipped'],
                datasets: [{{
                    data: [{len(sub['right_list'])}, {len(sub['wrong_list'])}, {len(sub['skip_list'])}],
                    backgroundColor: ['#10B981', '#EF4444', '#E2E8F0'],
                    borderWidth: 0,
                    hoverOffset: 4
                }}]
            }},
            options: {{
                plugins: {{ legend: {{ display: false }} }},
                cutout: '70%'
            }}
        }});
        """
        
    final_html = html_template.format(
        subject_cards=subject_cards_html,
        chart_scripts=chart_scripts,
        total_right=total_metrics['right'],
        total_wrong=total_metrics['wrong'],
        total_skip=total_metrics['skip'],
        total_score=total_metrics['score'],
        date=datetime.now().strftime("%d %b %Y, %I:%M %p")
    )
    
    with open(OUTPUT_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"\n[OK] Scorecard generated at: {OUTPUT_HTML_PATH}")

def main():
    print("\n[M] Medjeex Score Analysis Engine")
    print("-" * 35)

    # 1. Parse Answer Key (Dynamic)
    subjects, answer_map = parse_answer_key(ANSWER_KEY_PATH)
    if not subjects:
        print("[!] Error: No subjects detected in answer key. Check your headers.")
        return

    # 2. Get Attempts (From file or fallback)
    DEFAULT_ATTEMPTS = """
A-8,20,46,56,66,76,81,83,91,92,98,99,102,103,106,109,112,126,129,130,131,133,134,139,150,159,160,161,167,168,169,180
B-2,4,7,10,15,16,18,39,48,49,59,62,67,73,84,85,90,92,95,97,105,117,118,127,135,140,141,142,145,147,154,158,164,165
C-5,9,12,13,14,17,33,36,51,58,64,69,72,79,80,89,93,96,101,104,110,111,116,120,121,123,124,136,143,149,152,153,155,162,163,166,171,179
D-1,6,19,21,25,50,52,53,57,60,78,87,94,107,108,113,114,122,128,132,138,146,148,157,170,172,173,174,175,176
"""
    marked = parse_attempts(ATTEMPTS_PATH, DEFAULT_ATTEMPTS)
    print(f"[+] Loaded attempts for {len(marked)} questions.")

    # 3. Calculate Results
    results = []
    total_metrics = {"right": 0, "wrong": 0, "skip": 0, "score": 0, "bonus": 0, "ans_map": answer_map}
    
    for sub in subjects:
        sub_res = {
            "name": sub["name"], "emoji": sub["emoji"], "range": sub["range"],
            "right_list": [], "wrong_list": [], "skip_list": [], "bonus_list": [],
            "score": 0
        }
        
        start, end = sub["range"]
        for q in range(start, end + 1):
            correct_ans = answer_map.get(q)
            user_ans = marked.get(q)
            
            # 3.1 Handle Bonus
            if correct_ans == "Bonus":
                sub_res["bonus_list"].append(q)
                sub_res["score"] += SCORING["bonus"]
                total_metrics["score"] += SCORING["bonus"]
                total_metrics["bonus"] += 1
                continue
                
            if user_ans is None:
                sub_res["skip_list"].append(q)
                total_metrics["skip"] += 1
            else:
                # 3.2 Handle Multiple Correct (A/B)
                is_correct = False
                if isinstance(correct_ans, list):
                    if user_ans in correct_ans:
                        is_correct = True
                else:
                    if user_ans == correct_ans:
                        is_correct = True
                
                if is_correct:
                    sub_res["right_list"].append(q)
                    sub_res["score"] += SCORING["right"]
                    total_metrics["right"] += 1
                    total_metrics["score"] += SCORING["right"]
                else:
                    sub_res["wrong_list"].append((q, user_ans, correct_ans))
                    sub_res["score"] += SCORING["wrong"]
                    total_metrics["wrong"] += 1
                    total_metrics["score"] += SCORING["wrong"]
        
        results.append(sub_res)
    
    # 4. Console Summary
    print("\n" + "-"*35)
    for res in results:
        print(f"-> {res['name']}: {res['score']} Marks")
    print("-"*35)
    print(f"*** GRAND TOTAL: {total_metrics['score']} / 720")
    print("-"*35)
    
    # 5. Build HTML
    generate_html(results, total_metrics)

if __name__ == "__main__":
    main()
