from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import logging
from datetime import datetime, timedelta
from typing import Union
from pydantic_core import TzInfo
from pytz import timezone
import requests
import firebase_admin
import traceback
import functions_framework
import smtplib

from firebase_admin import credentials, firestore
from google.oauth2 import id_token
from flask import Flask, Request, Response, request, jsonify
from flask_cors import CORS
from google.cloud.firestore_v1.query_results import QueryResultsList
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from model_interfaces import generated_content
import model_interfaces.gemini_interface as gemini_interface
import model_interfaces.openai_interface as openai_interface
from prompts import get_match_concept_prompt

# Initialize Flask app and logging
# app = Flask(__name__)
# CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firestore DB
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Gmail API credentials
SERVICE_ACCOUNT_FILE = "jarvis-8ce89-20e9b84f7ab8.json"  # Add your service account file
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('gmail', 'v1', credentials=credentials)

def verify_oauth_token(token: str) -> Union[dict, None]:
    """Verify Google OAuth token and create user if needed."""
    logger.debug("Verifying OAuth token")
    try:
        token_info_url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
        response = requests.get(token_info_url)

        if response.status_code != 200:
            logger.warning(f"Token verification failed: {response.content}")
            return None

        token_info = response.json()
        google_user_id = token_info.get('sub')
        
        if not google_user_id:
            logger.warning("Google User ID not found in token")
            return None

        users_ref = db.collection('users')
        query = users_ref.where('google_user_id', '==', google_user_id)
        docs = list(query.stream())
        
        if not docs:
            users_ref.document(google_user_id).set({
                'google_user_id': google_user_id,
                'email': token_info.get('email')
            })
            
        return token_info

    except Exception as e:
        logger.error(f"Token verification error: {traceback.format_exc()}")
        return None

def get_user_timezone(request: Request) -> str:
    """Get user's timezone from Google Calendar API."""
    logger.debug("Getting user timezone")
    try:
        token = request.headers.get("Authorization")
        if token and token.startswith('Bearer '):
            token = token[len('Bearer '):]

        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        response = requests.get(user_info_url, headers=headers)

        if response.status_code == 200:
            # Get timezone
            timezone_url = "https://www.googleapis.com/calendar/v3/users/me/settings/timezone"
            timezone_response = requests.get(timezone_url, headers=headers)
            if timezone_response.status_code == 200:
                return timezone_response.json().get('value', 'America/New_York')

        return 'America/New_York'  # Default fallback
        
    except Exception as e:
        logger.error(f"Error getting timezone: {traceback.format_exc()}")
        return 'America/New_York'

def process_timestamp(timestamp_ms: int) -> dict:
    """Convert millisecond timestamp to formatted date."""
    date_time_obj = datetime.fromtimestamp(timestamp_ms / 1000)
    return {
        'formatted_date': date_time_obj.strftime('%m-%d-%Y'),
        'date_time_obj': date_time_obj
    }

def handle_cors_preflight(allowed_methods: str) -> Response:
    """Handle CORS preflight requests."""
    logger.debug("Handling CORS preflight")
    response = jsonify({'message': 'CORS preflight successful'})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    response.headers.add('Access-Control-Allow-Methods', allowed_methods)
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    return response

def handle_request_auth() -> Union[str, tuple]:
    """Authenticate request and return Google user ID."""
    logger.debug("Handling request authentication")
    token = request.headers.get('Authorization');
    
    if not token:
        response = jsonify({'error': 'Missing OAuth token'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 401

    if token.startswith('Bearer '):
        token = token[len('Bearer '):]

    google_token_info = verify_oauth_token(token)
    if not google_token_info:
        response = jsonify({'error': 'Invalid OAuth token'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 400

    google_user_id = google_token_info.get('sub')
    if not google_user_id:
        response = jsonify({'error': 'Invalid OAuth token'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 401
        
    return google_user_id


@functions_framework.http
def get_from_firestore(request):
    """Get notes from Firestore for the last 30 days."""
    logger.debug("Getting notes from Firestore")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('GET, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):
        return auth_result
    google_user_id = auth_result

    thirty_days_ago = datetime.now() - timedelta(days=30)
    notes_query = (db.collection('chrome_extension_notes')
                    .where('google_user_id', '==', google_user_id)
                    .where('date_time', '>=', thirty_days_ago)
                    .where('google_user_id', '==', google_user_id)
                    .order_by('date_time', 'DESCENDING')
                    .get())
    
    notes = [note.to_dict() for note in notes_query]
    response = jsonify({'notes': notes})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    return response, 200


@functions_framework.http
def write_to_firestore(request):
    """Write note to Firestore and generate summary."""
    logger.debug("Writing to Firestore")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('POST, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):
        return auth_result
    google_user_id = auth_result

    try:
        request_data = request.get_json()
        if not request_data or 'note' not in request_data or 'timestamp' not in request_data:
            logger.error('Missing required fields: note and timestamp')
            response = jsonify({'error': 'Missing required fields: note and timestamp'})
            response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
            return response, 400

        user_tz = get_user_timezone(request)
        date_time_obj = datetime.fromtimestamp(request_data['timestamp'] / 1000, tz=timezone(user_tz))
        note = request_data['note']

        # Generate headline using available AI service
        try:
            note_headline = openai_interface.generate_note_headline(note)
        except:
            note_headline = gemini_interface.generate_note_headline(note)

        # Write to Firestore
        logger.debug("Writing note to Firestore")
        notes_collection = 'chrome_extension_notes'
        count_query = db.collection(notes_collection).where('google_user_id', '==', google_user_id).count()
        pre_count = count_query.get()[0][0]
        logger.debug(f"Pre-write note count: {pre_count}")

        db.collection(notes_collection).add({
            'human_note': note,
            'note_headline': note_headline,
            'date_time': date_time_obj,
            'google_user_id': google_user_id
        })

        post_count = db.collection(notes_collection).where('google_user_id', '==', google_user_id).count().get()[0][0]
        logger.debug(f"Post-write note count: {post_count}")

        live_summary = get_live_summary(google_user_id)
        response = jsonify({'message': live_summary})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 200

    except Exception as e:
        logger.error(f"Error in write_to_firestore: {traceback.format_exc()}")
        response = jsonify({'error': 'Failed to process request'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 500


@functions_framework.http
def get_latest_summary(request):
    """Get most recent summary."""
    logger.debug("Getting latest summary")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('GET, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):
        return auth_result

    summary_object = query_firestore_for_latest_summary()
    if not summary_object:
        response = jsonify({'summary': "No summary available please try again later (server side error)"})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 404
    
    user_tz = get_user_timezone(request)
    current_time = datetime.now(timezone(user_tz))
    formatted_summary = construct_live_summary(current_time, summary_object['summary'])
    
    response = jsonify({'summary': formatted_summary})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    return response, 200


@functions_framework.http
def get_daily_digest(request):
    """Send daily digest emails to all users."""
    logger.debug("Getting daily digest")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('GET, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):
        return auth_result
    google_user_id = auth_result

    try:
        # Check if daily digest already sent today
        user_tz = get_user_timezone(request)
        current_time = datetime.now(timezone(user_tz))
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)

        digest_query = (db.collection("daily_digest")
                       .where('google_user_id', '==', google_user_id)
                       .where("date_time", ">=", start_of_day)
                       .where("date_time", "<=", end_of_day)
                       .limit(1)
                       .get())
        
        logger.info(len(digest_query))
        if len(digest_query) == 0:
            daily_digest = generated_content.construct_daily_digest(google_user_id)
            # Store the daily digest in Firestore
            db.collection("daily_digest").add({
                'digest': daily_digest,
                'date_time': current_time,
                'google_user_id': google_user_id
            })
        else:
            most_recent_digest = db.collection("daily_digest") \
                                .where('google_user_id', '==', google_user_id) \
                                .order_by("date_time", direction="DESCENDING") \
                                .limit(1) \
                                .get()
            logger.info(most_recent_digest[0])
            daily_digest = most_recent_digest[0].get('digest') if most_recent_digest else "No digest available"
        response = jsonify({'message': daily_digest})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 200

    except Exception as e:
        logger.error(f"Error in send_daily_digest: {str(e)}")
        response = jsonify({'error': 'Failed to send email'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 500


def query_firestore_for_latest_summary() -> Union[dict, None]:
    """Get most recent summary from Firestore."""
    logger.debug("Querying Firestore for latest summary")
    most_recent_summary = db.collection('live_summaries').order_by('date_time', direction='DESCENDING').limit(1).get()
    return most_recent_summary[0].to_dict() if most_recent_summary else None


def get_live_summary(google_user_id: str) -> str:
    """Generate live summary of user's recent notes."""
    logger.debug("Generating live summary")
    user_tz = get_user_timezone(request)
    current_time = datetime.now(timezone(user_tz))
    context_summary = generated_content.get_live_summary(google_user_id)
    db.collection('live_summaries').add({
        'summary': context_summary,
        'date_time': current_time,
        'google_user_id': google_user_id,
        'model': 'Gemini-1.5-Flash',
    })
    summary_count = db.collection('live_summaries').where('google_user_id', '==', google_user_id).count().get()[0][0]
    logger.debug(f"Total live summaries stored: {summary_count}")

    return construct_live_summary(current_time, context_summary)

def construct_live_summary(current_time: datetime, summary_text: str) -> str:
    """Format summary with current time and greeting."""
    logger.debug("Constructing formatted summary")
    formatted_date = current_time.strftime("%A, %B %d, %Y")
    formatted_time = current_time.strftime("%I:%M %p")
    hour = current_time.hour

    greeting = ("Good Morning" if 4 <= hour < 12 else
               "Good Afternoon" if 12 <= hour < 17 else
               "Good Evening")

    return f"""
    #{greeting}
    ##It is {formatted_time} on {formatted_date}

    ###Your Daily Digest:

    {summary_text}
    """


def get_note_concept(google_user_id, note):
    # Get all concepts for the user
    concepts = db.collection('concepts').where('google_user_id', '==', google_user_id).get()
    concept_object_list = [doc.to_dict() for doc in concepts]
    concepts = set([concept_object['concept'] for concept_object in concept_object_list if concept_object])
    concepts_string = "\n- ".join(concepts)
    # concepts = set(concepts)
    if concepts_string:
        concepts_string = "- " + concepts_string
    prompt = get_match_concept_prompt(note, concepts_string)
    concept_inference = gemini_interface.predict_text(prompt)
    return
