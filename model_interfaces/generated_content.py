from typing import List
import firebase_admin

from datetime import datetime, timedelta
from pytz import timezone
from firebase_admin import credentials, firestore

from model_interfaces.gemini_interface import predict_text
from prompts import LIVE_SUMMARY_PROMPT, TODAYS_TODO_PROMPT, YOUR_WEEK_AHEAD_PROMPT, YOUR_WEEK_IN_REVIEW_PROMPT

# Initialize Firestore DB
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
db = firestore.client()

def get_past_n_days_notes(google_user_id: str, n: int) -> List[str]:
    user_tz = 'America/New_York'
    current_time = datetime.now(timezone(user_tz))
    three_days_ago = current_time - timedelta(days=n)

    # Query recent notes
    notes_query = (db.collection("chrome_extension_notes")
                  .where('google_user_id', '==', google_user_id)
                  .where("date_time", ">=", three_days_ago)
                  .where("date_time", "<=", current_time)
                  .order_by("date_time", direction='DESCENDING'))

    return [f"Date: {doc.to_dict()['date_time']} note: {doc.to_dict()['human_note']}" for doc in notes_query.stream()]


def construct_daily_digest(google_user_id: str) -> str:
    """Stitches together the todo list, the week in review, and the next week's outlook."""
    todo_list = get_todo_list(google_user_id, get_past_n_days_notes(google_user_id, 3))
    last_week_notes = get_past_n_days_notes(google_user_id, 7)
    week_in_review = get_week_in_review(google_user_id, last_week_notes)
    next_week_outlook = get_next_week_outlook(google_user_id, last_week_notes, week_in_review, todo_list)
    return f"""\
    Your Daily Digest:

    {todo_list}

    {week_in_review}

    {next_week_outlook}
    """


def get_todo_list(google_user_id: str, three_days_notes: List[str]) -> str:
    full_prompt = TODAYS_TODO_PROMPT + "\n\n" + "\n".join(three_days_notes)
    return predict_text(full_prompt)


def get_week_in_review(google_user_id: str, last_week_notes: List[str]) -> str:
    full_prompt = YOUR_WEEK_IN_REVIEW_PROMPT + "\n\n" + "\n".join(last_week_notes)
    return predict_text(full_prompt)


def get_next_week_outlook(google_user_id: str, last_week_notes: List[str], last_week_summary: str, todays_todo_list: str) -> str:
    full_prompt = YOUR_WEEK_AHEAD_PROMPT + "\n\n" + f"Today's Tasks: \n {todays_todo_list}" + "\n\n" \
        + "One Week's Worth of Notes: \n".join(last_week_notes) + "\n\n" + f"Last Week's Summary: {last_week_summary}"
    return predict_text(full_prompt)


def get_live_summary(google_user_id: str) -> str:
    todays_notes = get_past_n_days_notes(google_user_id, 1)
    full_prompt = LIVE_SUMMARY_PROMPT + "\n\n" + "\n".join(todays_notes)
    return predict_text(full_prompt)
