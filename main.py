
import json
import logging 
from datetime import datetime, timedelta
from pydantic_core import TzInfo
from pytz import timezone
import requests
import firebase_admin
import traceback

from firebase_admin import credentials, firestore
from google.oauth2 import id_token
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud.firestore_v1.query_results import QueryResultsList
from google.cloud.firestore_v1.base_document import (
    DocumentSnapshot,
)

import model_interfaces.gemini_interface as gemini_interface
import model_interfaces.openai_interface as openai_interface

app = Flask(__name__)
CORS(app)
# logging.getLogger('flask_cors').level = logging.DEBUG

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__) 

# Initialize Firestore DB
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()  # Use Application Default Credentials
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to verify the token and get the user's Google ID (sub)
# Function to verify the access token using Google's Token Info API
def verify_oauth_token(token):
    logging.info("system log: verify_oauth_token.")
    try:
        # Verify the access token by calling Google's tokeninfo endpoint
        token_info_url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
        response = requests.get(token_info_url)

        if response.status_code == 200:
            # Parse the token information from the response
            token_info = response.json()

            # Extract the user's Google ID (sub) from the token info
            google_user_id = token_info.get('sub')
            if google_user_id:
                users_ref = db.collection('users')
                # Example query: Fetch documents where the 'age' field is greater than 30
                query = users_ref.where('google_user_id', '==', google_user_id)
                # Execute the query and get results
                docs = list(query.stream())
                if not docs:
                    users_ref.document(google_user_id).set({
                        'google_user_id': google_user_id,
                        'email': token_info.get('email')  # Save token info
                    })
                return token_info
            else:
                logging.info("Token verification failed: Google User ID not found in token")
                return None
        else:
            # The access token is invalid
            logging.info(f"Token verification failed: {response.content}")
            return None
    except Exception as e:
        error_details = traceback.format_exc()
        logging.info(f"Token verification failed: {error_details}")
        return None


def get_user_timezone(token) -> str:
    logging.info("system log: get_user_timezone.")
    try:
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[len('Bearer '):]
        # Get user info from Google API
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(user_info_url, headers=headers)

        if response.status_code == 200:
            # Get timezone from user's locale
            timezone_url = f"https://www.googleapis.com/calendar/v3/users/me/settings/timezone"
            timezone_response = requests.get(timezone_url, headers=headers)
            if timezone_response.status_code == 200:
                return timezone_response.json().get('value', 'America/New_York')
        return 'America/New_York'  # Default fallback
    except Exception as e:
        error_details = traceback.format_exc()
        logging.info(f"Error getting user timezone: {error_details}")
        return 'America/New_York'  # Default fallback


def process_timestamp(timestamp_ms):
    date_time_obj = datetime.fromtimestamp(timestamp_ms / 1000)
    return {
        'formatted_date': date_time_obj.strftime('%m-%d-%Y'),
        'date_time_obj': date_time_obj
    }


def handle_cors_preflight(allowed_methods):
    logging.info("system log: handle_cors_preflight.")
    response = jsonify({'message': 'CORS preflight successful'})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    response.headers.add('Access-Control-Allow-Methods', allowed_methods)
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    return response


def handle_request_auth():
    logging.info("system log: handle_request_auth.")
    token = request.headers.get('Authorization')
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


@app.route('/get_from_firestore', methods=['GET'])
def get_from_firestore(noop):
    logging.info("system log: get_from_firestore.")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('GET, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):  # Error response
        return auth_result
    google_user_id = auth_result

    thirty_days_ago = datetime.now() - timedelta(days=30)
    notes_query = db.collection('chrome_extension_notes') \
                    .where('date_time', '>=', thirty_days_ago) \
                    .where('google_user_id', '==',  google_user_id) \
                    .order_by('date_time', 'DESCENDING') \
                    .get()
    
    notes = [note.to_dict() for note in notes_query]
    response = jsonify({'notes': notes})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    return response, 200


# Main Cloud Function handler
# anchor
@app.route('/write_to_firestore', methods=['POST'])
def write_to_firestore(request):
    logging.debug("system log: write_to_firestore.")
    # Preflight
    if request.method == 'OPTIONS':
        return handle_cors_preflight('POST, OPTIONS')
    # Auth Check
    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):  # Error response
        return auth_result
    google_user_id = auth_result
    # Core Execution
    try:
        request_data = request.get_json()
        if not request_data or 'note' not in request_data or 'timestamp' not in request_data:
            logging.error('Missing required fields: note and timestamp')
            response = jsonify({'error': 'Missing required fields: note and timestamp'})
            response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
            return response, 400
        date_time_obj = datetime.fromtimestamp(request_data['timestamp'] / 1000, tz=timezone(get_user_timezone(request)))
        note = request_data['note']
    except Exception as e:
        error_details = traceback.format_exc()
        logging.error(f"Error parsing request data in write_to_firestore: {error_details}")
        response = jsonify({'error': f'Invalid request data: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 400
    try:
        # Generate note headline using available AI service
        try:
            note_headline = openai_interface.generate_note_headline(note)
        except:
            note_headline = gemini_interface.generate_note_headline(note)
        # Write to Firestore
        logging.debug("START write to firestore")
        count_query = db.collection('chrome_extension_notes123').where('google_user_id', '==', google_user_id).count()
        pre_count = count_query.get()[0][0]
        logger.debug(f"Number of Notes Stored Before: {pre_count}")
        db.collection('chrome_extension_notes123').add({
            'human_note': note,
            'note_headline': note_headline,
            'date_time': date_time_obj,
            'google_user_id': google_user_id
        })
        count_query = db.collection('chrome_extension_notes123').where('google_user_id', '==', google_user_id).count()
        post_count = count_query.get()[0][0]
        logger.debug(f"Number of Notes Stored After: {post_count}")
        logging.debug("END write to firestore")
        live_summary = get_live_summary(google_user_id)
        response = jsonify({'message': live_summary})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 200
    except Exception as e:
        error_details = traceback.format_exc()
        logging.error(f"Error in write_to_firestore: {error_details}")
        response = jsonify({'error': 'Failed to process request'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 500


@app.route('/get_latest_summary', methods=['GET'])
def get_latest_summary(noop):
    logging.info("system log: get_latest_summary.")
    if request.method == 'OPTIONS':
        return handle_cors_preflight('GET, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):  # Error response
        return auth_result
    summary_object = query_firestore_for_latest_summary()
    if not summary_object:
        response = jsonify({'summary': "No summary available please try again later (server side error)"})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 404
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[len('Bearer '):]
    user_tz = get_user_timezone(token)
    response = jsonify({'summary': construct_summary(datetime.now(timezone(user_tz)), summary_object['summary'])})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    return response, 200


def query_firestore_for_latest_summary():
    logging.info("system log: query_firestore_for_latest_summary.")
    most_recent_summary: QueryResultsList[DocumentSnapshot]  = db.collection('live_summaries').order_by('date_time', direction='DESCENDING').limit(1).get()
    return most_recent_summary[0].to_dict()


def get_live_summary(google_user_id: str):
    logging.info("system log: get_live_summary.")
    """Returns the summary of what has been going on in your day to day for the past week.
    """
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[len('Bearer '):]
    user_tz = get_user_timezone(token)
    
    now = datetime.now(timezone(user_tz))
    thirty_days_ago = now - timedelta(days=30)

    # Query Firestore collection for documents within the last 7 days, ordered by date_time descending
    notes_ref = db.collection("chrome_extension_notes")
    query = notes_ref.where("date_time", ">=", thirty_days_ago)\
                    .where("date_time", "<=", now)\
                    .order_by("date_time", direction='DESCENDING')

    notes_context = []
    results = query.stream()
    for doc in results:
        d = doc.to_dict()
        notes_context.append(f"Date: {d['date_time']} note: {d['human_note']}")
    
    context_summary = ''
    try:
        logger.info("openai_interface summary")
        context_summary = openai_interface.summarize(notes_context)
        model = 'gpt-4o'
    except:
        # Refactor this shit
        try:
            logger.info("gemini_interface summary")
            context_summary = gemini_interface.summarize(notes_context)
            model = 'gemini-1.5-flash'
        except:
            logger.info("query_firestore_for_latest_summary summary")
            summary_object = query_firestore_for_latest_summary()
            if summary_object:
                context_summary = summary_object['summary']
                model = summary_object['model']
            else:
                logger.info("No summary available. Please try again later.")
                context_summary = "No summary available. Please try again later."
                model = "N/A"

        live_summary = construct_summary(now, context_summary)
    

    # Add new summary
    db.collection('live_summaries').add({
        'summary': context_summary,
        'date_time': now,
        'google_user_id': google_user_id,
        'model': model,
    })
    count_query = db.collection('live_summaries').where('google_user_id', '==', google_user_id).count()
    count = count_query.get()[0][0]
    logger.info(f"Number of Live Summaries Stored: {count}")
    return live_summary

def construct_summary(datetime_now: datetime, summary_text: str):
    logging.info("system log: construct_summary.")
    formatted_date = datetime_now.strftime("%A, %B %d, %Y")
    formatted_time = datetime_now.strftime("%I:%M %p")  # Formats time as HH:MM AM/PM
    hour = datetime_now.hour

    if 4 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    return f"""
    #{greeting}
    ##It is {formatted_time} on {formatted_date}

    ###Live Context Summary:

    {summary_text}
    """

if __name__ == '__main__':
    app.run(debug=True)
