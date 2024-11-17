
import logging 
from datetime import datetime, timedelta
from pytz import timezone
import requests
import firebase_admin

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
logging.getLogger('flask_cors').level = logging.DEBUG

# Initialize Firestore DB
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()  # Use Application Default Credentials
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to verify the token and get the user's Google ID (sub)
# Function to verify the access token using Google's Token Info API
def verify_oauth_token(token):
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
                print("Token verification failed: Google User ID not found in token")
                return None
        else:
            # The access token is invalid
            print(f"Token verification failed: {response.content}")
            return None
    except Exception as e:
        # Any other errors
        print(f"Token verification failed: {e}")
        return None


def get_user_timezone(token):
    # Google API Key: AIzaSyBNY8f3W9Tki1i6OJaxVvLNvBiagfbkdR0
    try:
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
        print(f"Error getting user timezone: {e}")
        return 'America/New_York'  # Default fallback


def process_timestamp(timestamp_ms):
    date_time_obj = datetime.fromtimestamp(timestamp_ms / 1000)
    return {
        'formatted_date': date_time_obj.strftime('%m-%d-%Y'),
        'date_time_obj': date_time_obj
    }


def handle_cors_preflight(allowed_methods):
    response = jsonify({'message': 'CORS preflight successful'})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    response.headers.add('Access-Control-Allow-Methods', allowed_methods)
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    return response


def handle_request_auth():
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
def get_from_firestore(request):
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
@app.route('/write_to_firestore', methods=['POST'])
def write_to_firestore(request):
    if request.method == 'OPTIONS':
        return handle_cors_preflight('POST, OPTIONS')

    auth_result = handle_request_auth()
    if isinstance(auth_result, tuple):  # Error response
        return auth_result
    google_user_id = auth_result

    request_json = request.get_json(silent=True)
    # Check if the request has valid data to write
    if request_json and 'note' in request_json and 'timestamp' in request_json:
        note = request_json['note']
        date_time_obj = datetime.fromtimestamp(request_json['timestamp'] / 1000)
    else:
        response = jsonify({'error': 'Missing data to write'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 400

    try:
        try:
            note_headline = openai_interface.generate_note_headline(note)
        except:
            note_headline = gemini_interface.generate_note_headline(note)
        db.collection('chrome_extension_notes').add(
            {
                'human_note': note,
                'note_headline': note_headline,
                'date_time': date_time_obj,
                "google_user_id": google_user_id
            })
        live_summary = get_live_summary(google_user_id)
        response = jsonify({'message': live_summary})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        # print(f"Error writing to Firestore: {e}")
        print(f"Detailed Traceback: {error_details}")
        response = jsonify({'error': 'Failed to write data to Firestore'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 500


@app.route('/get_latest_summary', methods=['GET'])
def get_latest_summary(request):
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
    construct_summary(datetime.now(), summary_object['summary'])
    response = jsonify({'summary': construct_summary(datetime.now(), summary_object['summary'])})
    response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
    return response, 200


def query_firestore_for_latest_summary():
    most_recent_summary: QueryResultsList[DocumentSnapshot]  = db.collection('live_summaries').order_by('date_time', direction='DESCENDING').limit(1).get()
    return most_recent_summary[0].to_dict()


def get_live_summary(google_user_id: str):
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
        context_summary = openai_interface.summarize(notes_context)
        model = 'gpt-4o'
    except:
        # Refactor this shit
        try:
            context_summary = gemini_interface.summarize(notes_context)
            model = 'gemini-1.5-flash'
        except:
            summary_object = query_firestore_for_latest_summary()
            if summary_object:
                context_summary = summary_object['summary']
                model = summary_object['model']
            else:
                context_summary = "No summary available. Please try again later."
                model = "N/A"

        live_summary = construct_summary(now, context_summary)
    

    db.collection('live_summaries').add({
        'summary': context_summary,
        'date_time': now,
        'google_user_id': google_user_id,
        'model': model
    })
    return live_summary

def construct_summary(datetime_now: datetime, summary_text: str):
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
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
