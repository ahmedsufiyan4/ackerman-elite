import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import mysql.connector
import json
import re
import PyPDF2
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
from PIL import Image, ImageTk

MAIN_BG = "#ffffff"
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#34495e"
ACCENT_COLOR = "#e74c3c"
TEXT_DARK = "#2c3e50"
TEXT_LIGHT = "#95a5a6"
GRADIENT_BG = "#1a73e8"
GRADIENT_FG = "#4285f4"
ACCENT_COLOR = "#34a853"
TEXT_COLOR = "#202124"
SECONDARY_TEXT = "#5f6368"

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

import google.generativeai as genai

genai.configure(api_key="AIzaSyCoWXYSVyP27gh26uoWMSd3zh6aiC19G1s")

user_id = None

conn = mysql.connector.connect(
    host="localhost", user="root", password="yourmysqlpassword", database="akerman_elite"
)
cursor = conn.cursor()

def add_hover_effect(widget):
    def on_enter(e):
        widget.config(bg="#4CAF50", fg="white")
    def on_leave(e):
        widget.config(bg="#2C3E50", fg="white")
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def style_button(button, is_primary=True):
    if is_primary:
        button.configure(
            bg=GRADIENT_BG,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2"
        )
    else:
        button.configure(
            bg="white",
            fg=GRADIENT_BG,
            font=("Segoe UI", 12),
            bd=1,
            padx=25,
            pady=10,
            cursor="hand2"
        )
    def on_enter(e):
        button['bg'] = ACCENT_COLOR if is_primary else "#f8f9fa"
    def on_leave(e):
        button['bg'] = GRADIENT_BG if is_primary else "white"
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

def add_back_button(parent):
    back_frame = tk.Frame(parent, bg="white")
    back_frame.pack(fill=tk.X, pady=(10,0))
    def back_to_home():
        clear_window()
        if user_id:
            dashboard(user_id)
        else:
            create_home_ui()
    back_btn = tk.Button(
        back_frame,
        text="← Back",
        bg="white",
        fg="#4285f4",
        bd=0,
        font=("Arial", 10),
        command=back_to_home
    )
    back_btn.pack(side=tk.LEFT, padx=20)

def signup():
    def register_user():
        username = entry_username.get()
        email = entry_email.get()
        password = entry_password.get()
        confirm_pass = entry_confirm.get()
        if not all([username, email, password, confirm_pass]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        if password != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if not email.count("@") or not email.count("."):
            messagebox.showerror("Error", "Invalid email format")
            return
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                         (username, email, password))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            login()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Username or email already exists")
    clear_window()
    root.configure(bg="white")
    add_back_button(root)
    tk.Label(
        root,
        text="Sign Up",
        font=("Helvetica", 28, "bold"),
        fg="#4285f4",
        bg="white"
    ).pack(pady=(20,0))
    container = tk.Frame(root, bg="white")
    container.place(relx=0.5, rely=0.5, anchor="center")
    main_frame = tk.Frame(container, bg="white", bd=2, relief="solid")
    main_frame.pack(padx=40, pady=20)
    entry_username = tk.Entry(main_frame, width=40, font=("Helvetica", 12), bd=2, relief="solid")
    entry_email = tk.Entry(main_frame, width=40, font=("Helvetica", 12), bd=2, relief="solid")
    entry_password = tk.Entry(main_frame, width=40, font=("Helvetica", 12), show='•', bd=2, relief="solid")
    entry_confirm = tk.Entry(main_frame, width=40, font=("Helvetica", 12), show='•', bd=2, relief="solid")
    fields = [
        ("Username", entry_username),
        ("Email", entry_email),
        ("Password", entry_password),
        ("Confirm Password", entry_confirm)
    ]
    for lbl, entry in fields:
        tk.Label(
            main_frame,
            text=lbl,
            fg="#333333",
            bg="white",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", padx=20, pady=(15,5))
        entry.pack(pady=(0,10), ipady=8)
    btn_submit = tk.Button(
        main_frame,
        text="Create Account",
        bg="#4285f4",
        fg="white",
        font=("Helvetica", 14, "bold"),
        padx=30,
        pady=12,
        bd=0,
        cursor="hand2",
        command=register_user
    )
    btn_submit.pack(pady=30)
    login_frame = tk.Frame(main_frame, bg="white")
    login_frame.pack(pady=(0,20))
    tk.Label(
        login_frame,
        text="Already have an account?",
        fg="#666666",
        bg="white",
        font=("Helvetica", 10)
    ).pack(side=tk.LEFT)
    login_link = tk.Label(
        login_frame,
        text="Login",
        fg="#4285f4",
        bg="white",
        font=("Helvetica", 10, "bold"),
        cursor="hand2"
    )
    login_link.pack(side=tk.LEFT, padx=(5,0))
    login_link.bind("<Button-1>", lambda e: login())

def login():
    global user_id
    def validate_login():
        username, password = entry_username.get(), entry_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            dashboard(user_id)
        else:
            messagebox.showerror("Error", "Invalid Credentials")
    clear_window()
    root.configure(bg="white")
    add_back_button(root)
    container = tk.Frame(root, bg="white", padx=50, pady=30)
    container.pack(expand=True)
    main_frame = tk.Frame(container, bg="white", bd=2, relief="solid")
    main_frame.pack(padx=20, pady=20, ipadx=30, ipady=20)
    tk.Label(
        main_frame,
        text="Welcome Back!",
        font=("Helvetica", 28, "bold"),
        fg="#4285f4",
        bg="white"
    ).pack(pady=(20,10))
    tk.Label(
        main_frame,
        text="Sign in to continue",
        font=("Helvetica", 12),
        fg="#666666",
        bg="white"
    ).pack(pady=(0,20))
    entry_username = tk.Entry(
        main_frame,
        width=40,
        font=("Helvetica", 12),
        bd=2,
        relief="solid"
    )
    entry_password = tk.Entry(
        main_frame,
        width=40,
        font=("Helvetica", 12),
        show='•',
        bd=2,
        relief="solid"
    )
    for lbl, entry in zip(["Username", "Password"], [entry_username, entry_password]):
        tk.Label(
            main_frame,
            text=lbl,
            fg="#333333",
            bg="white",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", padx=20, pady=(15,5))
        entry.pack(pady=(0,10), ipady=8)
    btn_submit = tk.Button(
        main_frame,
        text="Login",
        bg="#4285f4",
        fg="white",
        font=("Helvetica", 14, "bold"),
        padx=30,
        pady=12,
        bd=0,
        cursor="hand2",
        command=validate_login
    )
    btn_submit.pack(pady=30)
    signup_frame = tk.Frame(main_frame, bg="white")
    signup_frame.pack(pady=(0,20))
    tk.Label(
        signup_frame,
        text="Don't have an account?",
        fg="#666666",
        bg="white",
        font=("Helvetica", 10)
    ).pack(side=tk.LEFT)
    signup_link = tk.Label(
        signup_frame,
        text="Sign Up",
        fg="#4285f4",
        bg="white",
        font=("Helvetica", 10, "bold"),
        cursor="hand2"
    )
    signup_link.pack(side=tk.LEFT, padx=(5,0))
    signup_link.bind("<Button-1>", lambda e: signup())

def determine_bloom_level(questions, user_answers):
    correct_answers = 0
    for idx, q in enumerate(questions):
        if user_answers[idx].get().split(". ")[0] == q["answer"]:
            correct_answers += 1
    return correct_answers

def save_progress(user_id, topic, bloom_level, questions, user_answers):
    clear_window()
    root.configure(bg="white")
    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(pady=20, fill="both", expand=True)
    canvas = tk.Canvas(main_frame, bg="white")
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    tk.Label(scrollable_frame, text="Quiz Results", font=("Arial", 24, "bold"), fg="#4285f4", bg="white").pack(pady=10)
    correct_answers = 0
    for idx, (q, user_ans) in enumerate(zip(questions, user_answers), 1):
        result_frame = tk.Frame(scrollable_frame, bg="white")
        result_frame.pack(fill="x", padx=20, pady=10)
        user_choice = user_ans.get().split(". ")[0]
        is_correct = user_choice == q["answer"]
        if is_correct:
            correct_answers += 1
        question_text = f"Q{idx}. {q['question']}"
        tk.Label(
            result_frame,
            text=question_text,
            fg="#333333",
            bg="white",
            font=("Arial", 12, "bold"),
            wraplength=600
        ).pack(anchor="w")
        result_color = "#34a853" if is_correct else "#ea4335"
        tk.Label(
            result_frame,
            text=f"Your answer: {user_ans.get()}",
            fg=result_color,
            bg="white",
            font=("Arial", 11)
        ).pack(anchor="w")
        if not is_correct:
            correct_option = next(opt for opt in q["options"] if opt.startswith(f"{q['answer']}."))
            tk.Label(
                result_frame,
                text=f"Correct answer: {correct_option}",
                fg="#34a853",
                bg="white",
                font=("Arial", 11, "bold")
            ).pack(anchor="w")
    score_frame = tk.Frame(scrollable_frame, bg="white")
    score_frame.pack(fill="x", padx=20, pady=20)
    tk.Label(
        score_frame,
        text=f"Total Score: {correct_answers}/5",
        fg="#4285f4",
        bg="white",
        font=("Arial", 14, "bold")
    ).pack()
    new_bloom_level = bloom_level + 1 if correct_answers >= 3 else bloom_level
    if correct_answers >= 3:
        cursor.execute("SELECT * FROM progress WHERE user_id=%s AND topic=%s", (user_id, topic))
        record = cursor.fetchone()
        if record:
            cursor.execute("UPDATE progress SET bloom_level=%s WHERE user_id=%s AND topic=%s", 
                         (new_bloom_level, user_id, topic))
        else:
            cursor.execute("INSERT INTO progress (user_id, topic, bloom_level) VALUES (%s, %s, %s)", 
                         (user_id, topic, new_bloom_level))
        conn.commit()
        message = f"Congratulations! Moving to level {new_bloom_level}"
    else:
        message = "Keep practicing to improve your score!"
    tk.Label(
        score_frame,
        text=message,
        fg="#666666",
        bg="white",
        font=("Arial", 12)
    ).pack(pady=10)


    button_frame = tk.Frame(scrollable_frame, bg="white")
    button_frame.pack(pady=20)
    

    btn_continue = tk.Button(
        button_frame,
        text="Continue",
        bg="#4285f4",
        fg="white",
        font=("Arial", 12),
        padx=20,
        pady=10,
        bd=0,
        command=lambda: update_and_return(user_id, topic, new_bloom_level)
    )
    btn_continue.pack(side=tk.LEFT, padx=10)
    
    if correct_answers >= 3:
        btn_next_level = tk.Button(
            button_frame,
            text="Try Next Level",
            bg="#34a853",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
            bd=0,
            command=lambda: display_quiz(user_id, generate_quiz(topic, new_bloom_level + 1), topic, new_bloom_level + 1)
        )
        btn_next_level.pack(side=tk.LEFT, padx=10)
    else:
        btn_retry = tk.Button(
            button_frame,
            text="Retry Level",
            bg="#ea4335",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
            bd=0,
            command=lambda: display_quiz(user_id, generate_quiz(topic, bloom_level), topic, bloom_level)
        )
        btn_retry.pack(side=tk.LEFT, padx=10)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
def update_and_return(user_id, topic, new_bloom_level):
    cursor.execute("SELECT * FROM progress WHERE user_id=%s AND topic=%s", (user_id, topic))
    record = cursor.fetchone()
    if record:
        cursor.execute("UPDATE progress SET bloom_level=%s WHERE user_id=%s AND topic=%s", 
                      (new_bloom_level, user_id, topic))
    else:
        cursor.execute("INSERT INTO progress (user_id, topic, bloom_level) VALUES (%s, %s, %s)", 
                      (user_id, topic, new_bloom_level))
    conn.commit()
    dashboard(user_id)

def generate_quiz(topic, bloom_level):
    if not genai:
        messagebox.showerror("Error", "AI service is not initialized")
        return None
        
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest') 
        prompt = f"""
            Generate a multiple-choice quiz on {topic} at Bloom's Taxonomy level {bloom_level}.
            - Include exactly 5 questions.
            - Each question should have 4 answer choices.
            - Include a "level" key specifying the Bloom's Taxonomy level (Remembering, Understanding, Applying, etc.).
            - Return output in valid JSON format: 
            [
                {{"question": "What is AI?", "options": ["A. option1", "B. option2", "C. option3", "D. option4"], "answer": "A"}},
                ...
            ]
        """
        
        response = model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("Empty response from AI")
            
        json_match = re.search(r"```json\n(.*)\n```", response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            try:
                return json.loads(response.text)
            except:
                raise ValueError("Invalid response format from AI")
    except Exception as e:
        messagebox.showerror("Error", f"Could not generate quiz: {str(e)}")
        return None

def chatbot_menu(user_id):
    clear_window()
    root.configure(bg="white")
    
    add_back_button(root)
    
    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(pady=20)
    
    tk.Label(main_frame, text="Choose Your Learning Method", font=("Arial", 24, "bold"), fg="#4285f4", bg="white").pack(pady=10)

    topic_frame = tk.Frame(main_frame, bg="white")
    topic_frame.pack(pady=20)
    tk.Label(topic_frame, text="Enter Topic Name", fg="#666666", bg="white", font=("Arial", 14)).pack()
    entry_topic = tk.Entry(topic_frame, width=50)
    entry_topic.pack(pady=5)
    
    tk.Label(main_frame, text="OR", font=("Arial", 16, "bold"), fg="#666666", bg="white").pack(pady=10)
    
    upload_frame = tk.Frame(main_frame, bg="white")
    upload_frame.pack(pady=20)
    tk.Label(upload_frame, text="Upload Your Document", fg="#666666", bg="white", font=("Arial", 14)).pack()
    
    document_path = tk.StringVar()
    
    def upload_file():
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("Word files", "*.docx"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            document_path.set(file_path)
            entry_topic.delete(0, tk.END) 
            file_name = file_path.split("/")[-1] 
            btn_upload.config(text=file_name)
    
    btn_upload = tk.Button(
        upload_frame,
        text="Choose File",
        bg="#4285f4",
        fg="white",
        font=("Arial", 12),
        padx=20,
        pady=5,
        bd=0,
        command=upload_file
    )
    btn_upload.pack(pady=5)
    
    def start_quiz():
        topic = entry_topic.get()
        doc_path = document_path.get()
        
        if topic:
            cursor.execute("SELECT bloom_level FROM progress WHERE user_id=%s AND topic=%s", (user_id, topic))
            record = cursor.fetchone()
            bloom_level = record[0] if record else 1
            quiz_questions = generate_quiz(topic, bloom_level)
            display_quiz(user_id, quiz_questions, topic, bloom_level)
        elif doc_path:
            try:
                content = ""
                if doc_path.lower().endswith('.pdf'):
                    with open(doc_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            content += page.extract_text()
                else:
                    with open(doc_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                
                tokens = word_tokenize(content.lower())
                stop_words = set(stopwords.words('english'))
                meaningful_words = [word for word in tokens if word.isalnum() and word not in stop_words]
                
                from collections import Counter
                word_freq = Counter(meaningful_words)
                main_topic = word_freq.most_common(1)[0][0].capitalize()
                
                cursor.execute("SELECT bloom_level FROM progress WHERE user_id=%s AND topic=%s", (user_id, main_topic))
                record = cursor.fetchone()
                bloom_level = record[0] if record else 1
                
                prompt = f"""
                Content: {content[:2000]}
                Based on this content, generate a quiz at Bloom's Taxonomy level {bloom_level}:
                - Include exactly 5 questions
                - Each question should have 4 answer choices
                - Return in JSON format:
                [
                    {{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "A"}}
                ]
                """
                quiz_questions = generate_quiz(prompt, bloom_level)
                display_quiz(user_id, quiz_questions, main_topic, bloom_level)
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not process the document: {str(e)}")
        else:
            messagebox.showerror("Error", "Please either enter a topic or upload a document")

    btn_submit = tk.Button(
        main_frame,
        text="Start Quiz",
        bg="#4285f4",
        fg="white",
        font=("Arial", 12),
        padx=20,
        pady=10,
        bd=0,
        command=start_quiz
    )
    btn_submit.pack(pady=20)
    
   

def dashboard(user_id):
    clear_window()
    root.configure(bg="white")
    
    top_frame = tk.Frame(root, bg=GRADIENT_BG)
    top_frame.pack(fill=tk.X)
    
    tk.Label(
        top_frame,
        text="Akerman Elite",
        font=("Montserrat", 24, "bold"),
        fg="white",
        bg=GRADIENT_BG
    ).pack(side=tk.LEFT, padx=20, pady=10)
    
    cursor.execute("SELECT username FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    username = user[0] if user else "User"
    
    tk.Label(
        top_frame,
        text=f"Welcome! {username}",
        font=("Segoe UI", 12),
        fg="white",
        bg=GRADIENT_BG
    ).pack(side=tk.RIGHT, padx=20, pady=10)
    
    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(pady=40, fill="both", expand=True)
    
    btn_quiz = tk.Button(
        main_frame,
        text="Start Learning!",
        command=lambda: chatbot_menu(user_id)
    )
    style_button(btn_quiz)
    btn_quiz.pack(pady=20)
    
    cursor.execute("SELECT topic, bloom_level FROM progress WHERE user_id=%s", (user_id,))
    records = cursor.fetchall()
    
    if records:
        tk.Label(main_frame, text="Your Progress", font=("Arial", 16, "bold"), fg="#4285f4", bg="white").pack(pady=10)
        for topic, bloom_level in records:
            record_frame = tk.Frame(main_frame, bg="white")
            record_frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(record_frame, text=f"Topic: {topic}", fg="#666666", bg="white", font=("Arial", 12)).pack(side=tk.LEFT)
            tk.Label(record_frame, text=f"Bloom Level: {bloom_level}", fg="#666666", bg="white", font=("Arial", 12)).pack(side=tk.RIGHT)
    else:
        tk.Label(main_frame, text="No learning progress yet!", fg="#666666", bg="white", font=("Arial", 12)).pack(pady=10)


def create_home_ui():
    root.configure(bg=MAIN_BG)
    
    header_frame = tk.Frame(root, bg=PRIMARY_COLOR)
    header_frame.pack(fill=tk.X)
    
    btn_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
    btn_frame.pack(anchor="ne", padx=20, pady=10)
    
    btn_login = tk.Button(
        btn_frame,
        text="Login",
        bg=PRIMARY_COLOR,
        fg="white",
        font=("Helvetica", 12),
        bd=0,
        padx=20,
        pady=5,
        cursor="hand2",
        command=login
    )
    btn_login.pack(side=tk.RIGHT, padx=5)
    
    btn_signup = tk.Button(
        btn_frame,
        text="Sign Up",
        bg="white",
        fg=PRIMARY_COLOR,
        font=("Helvetica", 12),
        bd=0,
        padx=20,
        pady=5,
        cursor="hand2",
        command=signup
    )
    btn_signup.pack(side=tk.RIGHT, padx=5)
    
    
    content_frame = tk.Frame(root, bg=MAIN_BG)
    content_frame.pack(expand=True, fill="both", pady=50)
    
    
    tk.Label(
        content_frame,
        text="Akerman Elite Learning",
        font=("Montserrat", 40, "bold"),
        fg="#0066cc",
        bg=MAIN_BG
    ).pack(pady=(0,10))
    
    tk.Label(
        content_frame,
        text="Your AI-Powered Learning Companion",
        font=("Helvetica", 18),
        fg=TEXT_LIGHT,
        bg=MAIN_BG
    ).pack(pady=(0,40))
    
    features_frame = tk.Frame(content_frame, bg=MAIN_BG)
    features_frame.pack(pady=20, padx=40)
    
    features = [
        ("📚 Personalized Learning with Bloom's Taxonomy"),
        ("🤖 AI-Generated Smart Assessments"),
        ("📊 Progress Tracking and Analytics"),
        ("📝 Upload Study Materials"),
        ("✨ Instant Feedback System" )
    ]
    
    for feature, color in features:
        feature_card = tk.Frame(features_frame, bg=color, bd=1, relief="solid")
        feature_card.pack(fill="x", pady=5, ipady=10)
        tk.Label(
            feature_card,
            text=feature,
            font=("Helvetica", 12),
            fg="white",
            bg=color,
            anchor="w",
            padx=20
        ).pack(fill="x")
    
    btn_get_started = tk.Button(
        content_frame,
        text="Start Learning Now",
        bg=ACCENT_COLOR,
        fg="white",
        font=("Helvetica", 14, "bold"),
        padx=40,
        pady=15,
        bd=0,
        cursor="hand2",
        command=login
    )
    btn_get_started.pack(pady=40)
    
    def on_enter(e):
        if e.widget == btn_login:
            e.widget.config(bg=SECONDARY_COLOR)
        elif e.widget == btn_signup:
            e.widget.config(bg="#f5f6fa")
        else:
            e.widget.config(bg="#c0392b")
            
    def on_leave(e):
        if e.widget == btn_login:
            e.widget.config(bg=PRIMARY_COLOR)
        elif e.widget == btn_signup:
            e.widget.config(bg="white")
        else:
            e.widget.config(bg=ACCENT_COLOR)
    
    for btn in [btn_login, btn_signup, btn_get_started]:
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
def display_quiz(user_id, questions, topic, bloom_level):
    if not questions:
        return
        
    clear_window()
    root.configure(bg="white")
    
    add_back_button(root)
    
    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(pady=20, fill="both", expand=True)
    

    canvas = tk.Canvas(main_frame, bg="white")
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    tk.Label(scrollable_frame, text=f"Quiz on {topic}", font=("Arial", 24, "bold"), fg="#4285f4", bg="white").pack(pady=10)
    
    user_answers = []
    for i, q in enumerate(questions, 1):
        question_frame = tk.Frame(scrollable_frame, bg="white")
        question_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(question_frame, text=f"Q{i}. {q['question']}", fg="#333333", bg="white", font=("Arial", 12), wraplength=600).pack(anchor="w")
        
        answer_var = tk.StringVar()
        for opt in q['options']:
            tk.Radiobutton(
                question_frame,
                text=opt,
                variable=answer_var,
                value=opt,
                bg="white",
                font=("Arial", 11)
            ).pack(anchor="w", pady=2)
        user_answers.append(answer_var)
    
    btn_submit = tk.Button(
        scrollable_frame,
        text="Submit",
        bg="#4285f4",
        fg="white",
        font=("Arial", 12),
        padx=20,
        pady=10,
        bd=0,
        command=lambda: save_progress(user_id, topic, bloom_level, questions, user_answers)
    )
    btn_submit.pack(pady=20)
    
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def create_ui():
    global root
    root = tk.Tk()
    root.title("Akerman Elite")
    root.geometry("800x500")
    icon_path = os.path.join(os.path.dirname(__file__),'logo.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    create_home_ui()
    root.mainloop()

create_ui()