"""Quiz Game - a Tkinter multiple-choice quiz.

Features: question categories, adaptive difficulty (Easy / Medium / Hard),
a countdown timer, a 50-50 lifeline, score tracking, a detailed results screen
and a leaderboard (Firebase, with a local JSON file as fallback).

Run with:  python quiz_game5.py
"""
import json
import os
import random
import tkinter as tk
from pathlib import Path
from tkinter import ttk

try:
    import requests
except ImportError:  # the game still works without it, scores are just saved locally
    requests = None

# ---------------------------------------------------------------- settings
# The Firebase address is not a password, but you can override it (or set it to "")
# with the QUIZ_FIREBASE_URL environment variable. "" means "local leaderboard only".
FIREBASE_BASE = os.environ.get("QUIZ_FIREBASE_URL", "https://quiz-game-23419-default-rtdb.firebaseio.com")
# Stored next to this script, so the same file is used no matter where you run it from
LOCAL_FILE = Path(__file__).with_name("local_leaderboard.json")
REQUEST_TIMEOUT = 5  # seconds to wait for Firebase before falling back to the local file

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]  # order matters: easiest -> hardest
MIN_QUIZ_LENGTH = 3
MAX_QUIZ_LENGTH = 10
DEFAULT_QUIZ_LENGTH = 5
TIME_PER_QUESTION = 20  # seconds
LOW_TIME_WARNING = 5    # timer turns red at or below this many seconds
MAX_NAME_LENGTH = 20
LEADERBOARD_SIZE = 10

# ---------------------------------------------------------------- look & feel
BG = "#f5f7fb"
TEXT = "#1f2937"
MUTED = "#6b7280"
PRIMARY = "#3b6ef5"
PRIMARY_DARK = "#2f58c4"
GOOD, GOOD_BG = "#1b7f4b", "#d8f3e3"
BAD, BAD_BG = "#c53030", "#fde2e2"
FONT = "Segoe UI"  # Tk falls back to a default font on systems without it
WRAP = 520         # pixel width before long text wraps

question_bank = {
    "General Knowledge": {
        "Easy": [
            {"question": "What is the capital of France?", "options": ["Paris", "London", "Berlin", "Rome"], "answer": "Paris"},
            {"question": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter", "Saturn"], "answer": "Mars"},
        ],
        "Medium": [
            {"question": "What is the largest mammal in the world?", "options": ["Elephant", "Blue Whale", "Shark", "Giraffe"], "answer": "Blue Whale"},
            {"question": "In which continent is the Sahara Desert located?", "options": ["Asia", "Africa", "Australia", "South America"], "answer": "Africa"},
        ],
        "Hard": [
            {"question": "Which is the smallest country in the world?", "options": ["Monaco", "Malta", "Vatican City", "Luxembourg"], "answer": "Vatican City"},
            {"question": "Which is the longest river in the world?", "options": ["Nile", "Amazon", "Yangtze", "Mississippi"], "answer": "Nile"},
        ],
    },
    "Science & Technology": {
        "Easy": [
            {"question": "Water boils at what temperature (Celsius)?", "options": ["50°C", "75°C", "100°C", "150°C"], "answer": "100°C"},
            {"question": "Which gas do plants absorb?", "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"], "answer": "Carbon Dioxide"},
        ],
        "Medium": [
            {"question": "Who developed Python programming language?", "options": ["Guido van Rossum", "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup"], "answer": "Guido van Rossum"},
            {"question": "Which part of the cell contains genetic material?", "options": ["Nucleus", "Cytoplasm", "Cell wall", "Mitochondria"], "answer": "Nucleus"},
        ],
        "Hard": [
            {"question": "What is the time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "answer": "O(log n)"},
            {"question": "What is the SI unit of electrical resistance?", "options": ["Volt", "Ohm", "Ampere", "Watt"], "answer": "Ohm"},
        ],
    },
    "History": {
        "Easy": [
            {"question": "Who was the first President of the USA?", "options": ["Abraham Lincoln", "George Washington", "John Adams", "Thomas Jefferson"], "answer": "George Washington"},
            {"question": "The Great Wall of China was built to protect against which group?", "options": ["Romans", "Mongols", "Huns", "Vikings"], "answer": "Mongols"},
        ],
        "Medium": [
            {"question": "In which year did World War II end?", "options": ["1939", "1945", "1950", "1942"], "answer": "1945"},
            {"question": "Who was known as the 'Iron Lady'?", "options": ["Indira Gandhi", "Margaret Thatcher", "Angela Merkel", "Golda Meir"], "answer": "Margaret Thatcher"},
        ],
        "Hard": [
            {"question": "The ancient city of Troy was located in which modern country?", "options": ["Italy", "Greece", "Turkey", "Egypt"], "answer": "Turkey"},
            {"question": "Who wrote the Indian national anthem?", "options": ["Rabindranath Tagore", "Mahatma Gandhi", "Bankim Chandra Chatterjee", "Sarojini Naidu"], "answer": "Rabindranath Tagore"},
        ],
    },
    "Sports": {
        "Easy": [
            {"question": "How many players are there in a cricket team?", "options": ["10", "11", "12", "9"], "answer": "11"},
            {"question": "Which sport uses a shuttlecock?", "options": ["Tennis", "Badminton", "Squash", "Table Tennis"], "answer": "Badminton"},
        ],
        "Medium": [
            {"question": "Which country hosted the 2016 Summer Olympics?", "options": ["China", "Brazil", "UK", "Russia"], "answer": "Brazil"},
            {"question": "Who holds the record for most goals in football history?", "options": ["Cristiano Ronaldo", "Lionel Messi", "Pelé", "Neymar"], "answer": "Cristiano Ronaldo"},
        ],
        "Hard": [
            {"question": "Which cricket player is known as 'The Wall'?", "options": ["Sachin Tendulkar", "Rahul Dravid", "Virat Kohli", "Ricky Ponting"], "answer": "Rahul Dravid"},
            {"question": "In which sport would you perform a slam dunk?", "options": ["Football", "Basketball", "Volleyball", "Tennis"], "answer": "Basketball"},
        ],
    },
    "Movies": {
        "Easy": [
            {"question": "Who directed the movie 'Titanic'?", "options": ["James Cameron", "Steven Spielberg", "Christopher Nolan", "Martin Scorsese"], "answer": "James Cameron"},
            {"question": "Which superhero is known as the Dark Knight?", "options": ["Superman", "Iron Man", "Batman", "Spider-Man"], "answer": "Batman"},
        ],
        "Medium": [
            {"question": "Which movie won the Oscar for Best Picture in 2020?", "options": ["Joker", "1917", "Parasite", "Ford v Ferrari"], "answer": "Parasite"},
            {"question": "Who played Jack Sparrow in 'Pirates of the Caribbean'?", "options": ["Brad Pitt", "Johnny Depp", "Leonardo DiCaprio", "Tom Cruise"], "answer": "Johnny Depp"},
        ],
        "Hard": [
            {"question": "In which year was the first Harry Potter film released?", "options": ["1999", "2001", "2003", "2005"], "answer": "2001"},
            {"question": "Who composed the music for 'Inception'?", "options": ["Hans Zimmer", "Alan Silvestri", "John Williams", "James Newton Howard"], "answer": "Hans Zimmer"},
        ],
    }
}


# ---------------------------------------------------------------- leaderboard data
# These functions only deal with data (no GUI), which keeps the class below shorter.

def count_questions(category):
    return sum(len(questions) for questions in question_bank[category].values())


def store_score(name, score):
    """Save a score. Returns "online", "local" or "failed"."""
    entry = {"name": name, "score": score}  # same structure the Firebase database already uses
    if save_score_online(entry):
        return "online"
    if save_score_local(entry):
        return "local"
    return "failed"


def save_score_online(entry):
    if requests is None or not FIREBASE_BASE:
        return False
    try:
        response = requests.post(f"{FIREBASE_BASE}/scores.json", json=entry, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return True
    except requests.RequestException:  # no internet, timeout, or Firebase refused the request
        return False


def read_local_entries():
    """Return the list stored in the local file. A missing file counts as an empty list."""
    try:
        with open(LOCAL_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except FileNotFoundError:
        return []
    if not isinstance(entries, list):
        raise ValueError("local leaderboard is not a list")
    return entries


def save_score_local(entry):
    try:
        try:
            entries = read_local_entries()
        except ValueError:  # file exists but is damaged: keep a copy instead of overwriting it
            os.replace(LOCAL_FILE, LOCAL_FILE.with_suffix(".corrupt.json"))
            entries = []
        entries.append(entry)
        # Write to a temporary file first so a crash can't leave a half-written leaderboard
        temp_file = LOCAL_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=4)
        os.replace(temp_file, LOCAL_FILE)
        return True
    except OSError:  # e.g. folder is read-only
        return False


def parse_scores(entries):
    """Turn raw leaderboard entries into (name, score) tuples, skipping malformed ones."""
    scores = []
    for entry in entries:
        try:
            scores.append((str(entry["name"]), int(entry["score"])))
        except (KeyError, TypeError, ValueError):
            continue
    return scores


def fetch_online_scores():
    """Return the Firebase scores, or an empty list if they can't be fetched."""
    if requests is None or not FIREBASE_BASE:
        return []
    try:
        response = requests.get(f"{FIREBASE_BASE}/scores.json", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):  # ValueError = reply wasn't valid JSON
        return []
    if not data:
        return []
    return parse_scores(data.values() if isinstance(data, dict) else data)


def get_leaderboard():
    """Return (scores, source) with source "online", "local" or "none". Best score first."""
    scores, source = fetch_online_scores(), "online"
    if not scores:  # offline or empty: use the local file instead
        try:
            scores = parse_scores(read_local_entries())
        except (OSError, ValueError):
            scores = []
        source = "local" if scores else "none"
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores[:LEADERBOARD_SIZE], source


# ---------------------------------------------------------------- the game
class QuizGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Game")
        self.root.geometry("600x740")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.setup_styles()

        # Choices remembered between quizzes
        self.player_name = ""
        self.category = list(question_bank)[0]
        self.requested_length = DEFAULT_QUIZ_LENGTH

        # Timer/screen bookkeeping (see stop_timer and clear_screen)
        self.timer_after_id = None
        self.answered = True
        self.question_id = 0   # changes for every question, so old timer callbacks can be ignored
        self.screen_id = 0     # changes for every screen, so delayed callbacks can be ignored
        self.save_status = ""

        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=24, pady=20)
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.show_menu()

    # ------------------------------------------------------------ styling
    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")  # unlike the default Windows theme, "clam" allows coloured buttons

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=(FONT, 11))
        style.configure("Title.TLabel", font=(FONT, 26, "bold"))
        style.configure("Heading.TLabel", font=(FONT, 14, "bold"))
        style.configure("Muted.TLabel", foreground=MUTED, font=(FONT, 10))
        style.configure("Question.TLabel", font=(FONT, 15, "bold"))
        style.configure("Timer.TLabel", foreground=PRIMARY, font=(FONT, 12, "bold"))
        style.configure("TimerLow.TLabel", foreground=BAD, font=(FONT, 12, "bold"))
        style.configure("Good.TLabel", foreground=GOOD, font=(FONT, 12, "bold"))
        style.configure("Bad.TLabel", foreground=BAD, font=(FONT, 12, "bold"))
        style.configure("BigScore.TLabel", font=(FONT, 30, "bold"), foreground=PRIMARY)
        style.configure("StatValue.TLabel", font=(FONT, 18, "bold"))
        style.configure("TLabelframe", background=BG, bordercolor="#c9d1e3")
        style.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=(FONT, 10, "bold"))
        style.configure("Treeview", font=(FONT, 11), rowheight=28, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=(FONT, 11, "bold"))
        style.configure("Quiz.Horizontal.TProgressbar", troughcolor="#dfe5f1", background=PRIMARY,
                        bordercolor=BG, lightcolor=PRIMARY, darkcolor=PRIMARY)

        def button_style(name, bg, fg, hover, disabled_bg, disabled_fg, size=11, padding=(12, 9)):
            style.configure(name, background=bg, foreground=fg, font=(FONT, size), padding=padding,
                            bordercolor="#c9d1e3", lightcolor=bg, darkcolor=bg, focuscolor=bg)
            style.map(name,
                      background=[("disabled", disabled_bg), ("active", hover)],
                      foreground=[("disabled", disabled_fg)],
                      lightcolor=[("disabled", disabled_bg), ("active", hover)],
                      darkcolor=[("disabled", disabled_bg), ("active", hover)])

        button_style("TButton", "#e5e9f2", TEXT, "#d6dcea", "#eceff5", "#9ca3af")
        button_style("Primary.TButton", PRIMARY, "white", PRIMARY_DARK, "#a9bcf5", "white")
        button_style("Lifeline.TButton", "#fff1d6", "#8a5a00", "#ffe3a8", "#f1f3f8", "#9ca3af")
        button_style("Option.TButton", "white", TEXT, "#eef2ff", "#f1f3f8", "#9ca3af", size=12, padding=(14, 12))
        button_style("Correct.TButton", GOOD_BG, GOOD, GOOD_BG, GOOD_BG, GOOD, size=12, padding=(14, 12))
        button_style("Wrong.TButton", BAD_BG, BAD, BAD_BG, BAD_BG, BAD, size=12, padding=(14, 12))

    # ------------------------------------------------------------ screen management
    def clear_screen(self):
        """Remove the current screen. Also invalidates any timer or delayed callback still pending."""
        self.stop_timer()
        self.question_id += 1
        self.screen_id += 1
        for widget in self.container.winfo_children():
            widget.destroy()

    def close_window(self):
        self.stop_timer()
        self.root.destroy()

    # ------------------------------------------------------------ main menu
    def show_menu(self):
        self.clear_screen()
        c = self.container
        ttk.Label(c, text="Quiz Game", style="Title.TLabel").pack(pady=(30, 4))
        ttk.Label(c, text="Test your knowledge - the difficulty adapts as you play.",
                  style="Muted.TLabel").pack(pady=(0, 28))

        form = ttk.Frame(c)
        form.pack(fill="x", padx=40)
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Your name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=self.player_name)
        name_entry = ttk.Entry(form, textvariable=self.name_var, font=(FONT, 12))
        name_entry.grid(row=1, column=0, sticky="ew", pady=(2, 2))
        ttk.Label(form, text=f"Up to {MAX_NAME_LENGTH} characters. Leave blank to play as 'Player'.",
                  style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 14))

        ttk.Label(form, text="Category").grid(row=3, column=0, sticky="w")
        self.category_var = tk.StringVar(value=self.category)
        category_box = ttk.Combobox(form, textvariable=self.category_var, values=list(question_bank),
                                    state="readonly", font=(FONT, 12))
        category_box.grid(row=4, column=0, sticky="ew", pady=(2, 14))
        category_box.bind("<<ComboboxSelected>>", self.update_length_choices)

        ttk.Label(form, text="Number of questions").grid(row=5, column=0, sticky="w")
        self.length_var = tk.StringVar()
        self.length_box = ttk.Combobox(form, textvariable=self.length_var, state="readonly", font=(FONT, 12))
        self.length_box.grid(row=6, column=0, sticky="ew", pady=(2, 0))
        self.update_length_choices()

        ttk.Button(c, text="Start Quiz", style="Primary.TButton",
                   command=self.start_from_menu).pack(fill="x", padx=40, pady=(30, 8))
        ttk.Button(c, text="View Leaderboard",
                   command=lambda: self.show_leaderboard(self.show_menu)).pack(fill="x", padx=40, pady=4)
        ttk.Button(c, text="Quit", command=self.close_window).pack(fill="x", padx=40, pady=4)

        name_entry.bind("<Return>", lambda event: self.start_from_menu())
        name_entry.focus_set()

    def update_length_choices(self, event=None):
        """Offer only quiz lengths the chosen category can actually supply."""
        top = min(MAX_QUIZ_LENGTH, count_questions(self.category_var.get()))
        choices = list(range(min(MIN_QUIZ_LENGTH, top), top + 1))
        self.length_box.config(values=choices)
        keep = self.requested_length if self.requested_length in choices else min(DEFAULT_QUIZ_LENGTH, top)
        self.length_var.set(str(keep))

    def start_from_menu(self):
        """Read and validate the menu choices, then start the quiz."""
        self.player_name = self.name_var.get().strip()[:MAX_NAME_LENGTH] or "Player"
        category = self.category_var.get()
        self.category = category if category in question_bank else list(question_bank)[0]
        try:
            self.requested_length = int(self.length_var.get())
        except ValueError:
            self.requested_length = DEFAULT_QUIZ_LENGTH
        self.start_quiz()

    # ------------------------------------------------------------ quiz setup
    def start_quiz(self):
        """Reset everything for a new quiz and show the first question."""
        # Copy the lists so removing used questions never changes the original question bank
        self.questions_by_difficulty = {level: list(qs) for level, qs in question_bank[self.category].items()}
        # A quiz can never be longer than the number of questions available
        self.quiz_length = min(self.requested_length, count_questions(self.category))

        self.score = 0
        self.level = "Easy"
        self.current_question = None
        self.lifeline_used = False
        self.questions_asked = 0
        self.results = []  # one entry per question, used by the results screen
        self.build_quiz_screen()
        self.load_question()

    def build_quiz_screen(self):
        self.clear_screen()
        c = self.container

        header = ttk.Frame(c)
        header.pack(fill="x")
        ttk.Label(header, text=f"{self.player_name}  |  {self.category}", style="Muted.TLabel").pack(side="left")
        self.score_label = ttk.Label(header, text="Score: 0", style="Heading.TLabel")
        self.score_label.pack(side="right")

        self.progress_label = ttk.Label(c, text="", style="Muted.TLabel")
        self.progress_label.pack(anchor="w", pady=(16, 4))
        self.progress_bar = ttk.Progressbar(c, style="Quiz.Horizontal.TProgressbar", mode="determinate",
                                            maximum=max(self.quiz_length, 1))
        self.progress_bar.pack(fill="x")

        self.timer_label = ttk.Label(c, text="", style="Timer.TLabel")
        self.timer_label.pack(anchor="e", pady=(10, 0))
        self.question_label = ttk.Label(c, text="", style="Question.TLabel", wraplength=WRAP, justify="left")
        self.question_label.pack(anchor="w", pady=(4, 18))

        self.option_buttons = []
        for i in range(4):
            button = ttk.Button(c, text="", style="Option.TButton", command=lambda i=i: self.check_answer(i))
            button.pack(fill="x", pady=5)
            self.option_buttons.append(button)

        # Fixed-height box so the buttons below don't jump when feedback appears
        feedback_box = ttk.Frame(c, height=60)
        feedback_box.pack(fill="x", pady=(8, 4))
        feedback_box.pack_propagate(False)
        self.feedback_label = ttk.Label(feedback_box, text="", style="Good.TLabel", wraplength=WRAP, justify="left")
        self.feedback_label.pack(anchor="w", pady=4)

        bottom = ttk.Frame(c)
        bottom.pack(fill="x")
        self.lifeline_button = ttk.Button(bottom, text="50-50 Lifeline", style="Lifeline.TButton",
                                          command=self.use_lifeline)
        self.lifeline_button.pack(side="left")
        self.next_button = ttk.Button(bottom, text="Next Question", style="Primary.TButton",
                                      command=self.go_next, state="disabled")
        self.next_button.pack(side="right")

    # ------------------------------------------------------------ question flow
    def get_question(self):
        """Return an unused question, preferring the current difficulty.

        If the current difficulty has no questions left, fall back to the
        nearest difficulty that still has some. Returns None only when every
        difficulty is empty.
        """
        current_index = DIFFICULTY_LEVELS.index(self.level)
        # sorted() is stable, so when two levels are equally close the easier one wins
        levels_by_distance = sorted(
            DIFFICULTY_LEVELS, key=lambda lvl: abs(DIFFICULTY_LEVELS.index(lvl) - current_index))

        for level in levels_by_distance:
            available = self.questions_by_difficulty.get(level, [])
            if available:
                self.level = level  # keep the on-screen level and the adaptive logic in sync
                # pop() removes the question, so it can't be asked again in this quiz
                return available.pop(random.randrange(len(available)))
        return None

    def load_question(self):
        self.stop_timer()

        # The quiz ends when the chosen length is reached (or, as a safety net, nothing is left to ask)
        if self.questions_asked >= self.quiz_length:
            self.show_results()
            return
        self.current_question = self.get_question()
        if self.current_question is None:
            self.show_results()
            return

        self.questions_asked += 1
        self.answered = False
        self.question_id += 1
        self.time_left = TIME_PER_QUESTION
        q = self.current_question

        self.progress_label.config(text=f"Question {self.questions_asked} of {self.quiz_length}   |   {self.level}")
        self.progress_bar.config(value=self.questions_asked)
        self.question_label.config(text=q["question"])
        self.timer_label.config(text=f"Time left: {self.time_left}s", style="Timer.TLabel")
        self.feedback_label.config(text="")

        for button, option in zip(self.option_buttons, q["options"]):
            button.config(text=option, state="normal", style="Option.TButton")
        self.lifeline_button.config(state="disabled" if self.lifeline_used else "normal")
        is_last = self.questions_asked >= self.quiz_length
        self.next_button.config(text="See Results" if is_last else "Next Question", state="disabled")

        # The first tick happens one second from now, so the full time is shown at the start
        self.schedule_tick()

    def go_next(self):
        if self.answered:  # the button is only enabled after answering, this is just a safety check
            self.load_question()

    def check_answer(self, choice_index):
        # Only the first answer counts; ignore any extra clicks
        if self.answered or self.current_question is None:
            return
        self.lock_answers()

        q = self.current_question
        selected = q["options"][choice_index]
        is_correct = selected == q["answer"]

        if is_correct:
            self.score += 1
            self.score_label.config(text=f"Score: {self.score}")
            self.show_feedback("Correct! Well done.", good=True)
        else:
            self.show_feedback(f"Incorrect. The correct answer is: {q['answer']}", good=False)
        self.highlight_answers(chosen_index=choice_index)
        self.finish_question(selected, "correct" if is_correct else "incorrect")

    def handle_timeout(self):
        self.lock_answers()
        self.show_feedback(f"Time's up! The correct answer is: {self.current_question['answer']}", good=False)
        self.highlight_answers(chosen_index=None)
        self.finish_question(None, "unanswered")

    def finish_question(self, chosen, status):
        """Record the outcome, adapt the difficulty and let the player continue."""
        q = self.current_question
        self.results.append({"question": q["question"], "correct_answer": q["answer"],
                             "chosen": chosen, "status": status})
        self.adjust_level(status == "correct")
        self.next_button.config(state="normal")

    def adjust_level(self, was_correct):
        """Move one level up after a correct answer, one level down otherwise."""
        index = DIFFICULTY_LEVELS.index(self.level) + (1 if was_correct else -1)
        self.level = DIFFICULTY_LEVELS[max(0, min(index, len(DIFFICULTY_LEVELS) - 1))]

    def show_feedback(self, message, good):
        self.feedback_label.config(text=message, style="Good.TLabel" if good else "Bad.TLabel")

    def highlight_answers(self, chosen_index):
        """Colour the correct option green and (if the player picked one) a wrong choice red."""
        q = self.current_question
        for index, option in enumerate(q["options"]):
            if option == q["answer"]:
                self.option_buttons[index].config(style="Correct.TButton")
            elif index == chosen_index:
                self.option_buttons[index].config(style="Wrong.TButton")

    def lock_answers(self):
        """Mark the question as finished and disable every button that could still be clicked."""
        self.answered = True
        self.stop_timer()
        for button in self.option_buttons:
            button.config(state="disabled")
        self.lifeline_button.config(state="disabled")

    def use_lifeline(self):
        # One use per quiz, and never after the question has been answered or timed out
        if self.lifeline_used or self.answered or self.current_question is None:
            return
        q = self.current_question
        # Work from the question data (not the button text) so the correct answer can never be removed
        wrong_indices = [i for i, option in enumerate(q["options"]) if option != q["answer"]]
        for i in random.sample(wrong_indices, min(2, len(wrong_indices))):
            self.option_buttons[i].config(text="-", state="disabled")

        self.lifeline_used = True
        self.lifeline_button.config(state="disabled")

    # ------------------------------------------------------------ timer
    def stop_timer(self):
        """Cancel the pending timer tick, if there is one."""
        if self.timer_after_id is not None:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def schedule_tick(self):
        # Remember which question this tick belongs to
        self.timer_after_id = self.root.after(1000, lambda qid=self.question_id: self.update_timer(qid))

    def update_timer(self, question_id):
        self.timer_after_id = None
        # Ignore a leftover callback from an earlier question, or one that arrives after answering
        if question_id != self.question_id or self.answered:
            return

        self.time_left -= 1
        low = self.time_left <= LOW_TIME_WARNING
        self.timer_label.config(text=f"Time left: {self.time_left}s", style="TimerLow.TLabel" if low else "Timer.TLabel")
        if self.time_left > 0:
            self.schedule_tick()
        else:
            self.handle_timeout()

    # ------------------------------------------------------------ results screen
    def show_results(self, save=True):
        """Show the summary. save=False re-displays it (e.g. coming back from the leaderboard)."""
        self.clear_screen()
        c = self.container

        correct = sum(1 for r in self.results if r["status"] == "correct")
        incorrect = sum(1 for r in self.results if r["status"] == "incorrect")
        unanswered = sum(1 for r in self.results if r["status"] == "unanswered")
        attempted = correct + incorrect  # questions the player actually answered
        accuracy = round(correct / attempted * 100) if attempted else 0

        ttk.Label(c, text="Quiz Complete!", style="Title.TLabel").pack(pady=(4, 0))
        ttk.Label(c, text=f"{self.player_name}  |  {self.category}", style="Muted.TLabel").pack()
        ttk.Label(c, text=f"{self.score} / {self.quiz_length}", style="BigScore.TLabel").pack(pady=(8, 0))
        ttk.Label(c, text=f"Questions attempted: {attempted} of {self.quiz_length}",
                  style="Muted.TLabel").pack()

        stats = ttk.Frame(c)
        stats.pack(fill="x", pady=(14, 0))
        for column, (label, value) in enumerate([("Correct", correct), ("Incorrect", incorrect),
                                                 ("Unanswered", unanswered), ("Accuracy", f"{accuracy}%")]):
            stats.columnconfigure(column, weight=1)
            ttk.Label(stats, text=str(value), style="StatValue.TLabel").grid(row=0, column=column)
            ttk.Label(stats, text=label, style="Muted.TLabel").grid(row=1, column=column)

        review = ttk.LabelFrame(c, text="Questions to review", padding=8)
        review.pack(fill="both", expand=True, pady=(14, 6))
        text = tk.Text(review, height=8, wrap="word", font=(FONT, 10), bg="white", relief="flat",
                       borderwidth=0, padx=8, pady=6)
        scrollbar = ttk.Scrollbar(review, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.tag_configure("question", font=(FONT, 10, "bold"))
        text.tag_configure("yours", foreground=BAD)
        text.tag_configure("answer", foreground=GOOD)

        missed = [r for r in self.results if r["status"] != "correct"]
        if not missed:
            text.insert("end", "Perfect score - you didn't miss a single question!", "answer")
        for number, r in enumerate(missed, start=1):
            text.insert("end", f"{number}. {r['question']}\n", "question")
            text.insert("end", f"    Your answer: {r['chosen'] or 'No answer (time ran out)'}\n", "yours")
            text.insert("end", f"    Correct answer: {r['correct_answer']}\n\n", "answer")
        text.config(state="disabled")  # read-only

        self.save_label = ttk.Label(c, text=self.save_status, style="Muted.TLabel", wraplength=WRAP)
        self.save_label.pack(pady=(0, 8))

        # 2x2 grid with equal column widths so all four buttons line up
        buttons = ttk.Frame(c)
        buttons.pack(fill="x")
        buttons.columnconfigure((0, 1), weight=1, uniform="buttons")
        ttk.Button(buttons, text="Play Again", style="Primary.TButton",
                   command=self.start_quiz).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
        ttk.Button(buttons, text="Main Menu",
                   command=self.show_menu).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)
        ttk.Button(buttons, text="View Leaderboard",
                   command=lambda: self.show_leaderboard(lambda: self.show_results(save=False))
                   ).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.copy_button = ttk.Button(buttons, text="Copy Result", command=self.copy_result)
        self.copy_button.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

        if save:
            self.save_label.config(text="Saving your score...")
            # Short delay so the results appear before the (possibly slow) network call starts
            self.root.after(100, lambda sid=self.screen_id: self.save_and_report(sid))

    def save_and_report(self, screen_id):
        if screen_id != self.screen_id:  # player already left this screen
            return
        outcome = store_score(self.player_name, self.score)
        self.save_status = {
            "online": "Score saved to the online leaderboard.",
            "local": "Online leaderboard unavailable - score saved on this computer instead.",
            "failed": "Could not save your score (online and local saving both failed).",
        }[outcome]
        self.save_label.config(text=self.save_status)

    def copy_result(self):
        share_text = f"{self.player_name} scored {self.score} points in the Quiz Game!"
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(share_text)
            self.copy_button.config(text="Copied!")
        except tk.TclError:  # clipboard not available
            self.copy_button.config(text="Copy failed")

    # ------------------------------------------------------------ leaderboard screen
    def show_leaderboard(self, go_back):
        """Show the top scores. go_back is the function the Back button calls."""
        self.clear_screen()
        c = self.container
        ttk.Label(c, text="Leaderboard", style="Title.TLabel").pack(pady=(10, 4))
        self.board_status = ttk.Label(c, text="Loading...", style="Muted.TLabel", wraplength=WRAP)
        self.board_status.pack(pady=(0, 14))

        self.board = ttk.Treeview(c, columns=("rank", "name", "score"), show="headings", height=LEADERBOARD_SIZE)
        for column, title, width, anchor in (("rank", "#", 60, "center"), ("name", "Player", 330, "w"),
                                             ("score", "Score", 100, "center")):
            self.board.heading(column, text=title)
            self.board.column(column, width=width, anchor=anchor)
        self.board.pack(fill="x")

        ttk.Button(c, text="Back", style="Primary.TButton", command=go_back).pack(fill="x", pady=(20, 0))
        # Delay so "Loading..." is visible while the network request runs
        self.root.after(100, lambda sid=self.screen_id: self.fill_leaderboard(sid))

    def fill_leaderboard(self, screen_id):
        if screen_id != self.screen_id:
            return
        scores, source = get_leaderboard()
        for rank, (name, score) in enumerate(scores, start=1):
            self.board.insert("", "end", values=(rank, name, score))
        self.board_status.config(text={
            "online": "Online leaderboard - top 10",
            "local": "Offline - showing scores saved on this computer",
            "none": "No scores yet. Finish a quiz to be the first!",
        }[source])


def main():
    root = tk.Tk()
    QuizGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
