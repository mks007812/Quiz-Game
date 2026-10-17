# Quiz Game

A desktop multiple-choice quiz built with **Python and Tkinter**. Pick a category and quiz length,
answer against a countdown timer, and compare your score on a leaderboard.

## Features
- 5 categories (General Knowledge, Science & Technology, History, Sports, Movies) with Easy / Medium / Hard questions
- Adaptive difficulty: correct answers move you up a level, wrong answers or timeouts move you down
- 20-second countdown per question
- One-time 50-50 lifeline
- Inline feedback (green / red) and a progress bar - no pop-up boxes
- Results screen: score, attempted, accuracy, correct / incorrect / unanswered counts, and the correct answers for every question you missed
- Leaderboard: Firebase Realtime Database, with automatic fallback to a local JSON file when offline

## Run it
```
pip install -r requirements.txt
python quiz_game5.py
```
Python 3.9+ with Tkinter (included in the standard Windows installer from python.org).
The game also works without `requests` - scores are then saved locally only.

## Project layout
| File | Purpose |
|---|---|
| `quiz_game5.py` | The whole game: question bank, leaderboard functions, GUI |
| `local_leaderboard.json` | Offline scores (created automatically) |
| `requirements.txt` | Third-party dependency (`requests`) |

## Configuration
- `QUIZ_FIREBASE_URL` environment variable overrides the Firebase address. Set it to an empty
  string to use the local leaderboard only.
- Quiz length, time per question and other settings are constants at the top of `quiz_game5.py`.

## Firebase note
The game writes `{"name": ..., "score": ...}` entries to `/scores`. Because the game has no login,
anyone who knows the database URL can add scores, so restrict your Realtime Database
**rules** to allow only reads and *new* entries of the right shape (no overwriting or deleting).
Never put admin keys or service-account files in this repository.
