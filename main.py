
import logging 
from datetime import datetime, timedelta
import requests
import firebase_admin

from firebase_admin import credentials, firestore
from google.oauth2 import id_token
from flask import Flask, request, jsonify
from flask_cors import CORS

from note_processor import generate_note_headline, summarize_note

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


def process_timestamp(timestamp_ms):
    date_time_obj = datetime.fromtimestamp(timestamp_ms / 1000)
    return {
        'formatted_date': date_time_obj.strftime('%m-%d-%Y'),
        'date_time_obj': date_time_obj
    }


@app.route('/get_from_firestore', methods=['GET'])
def get_from_firestore(request):
    if request.method == 'OPTIONS':
        # CORS preflight request - respond with allowed methods and headers
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        return response
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

    seven_days_ago = datetime.now() - timedelta(days=7)
    notes_query = db.collection('chrome_extension_notes') \
                    .where('date_time', '>=', seven_days_ago) \
                    .where('google_user_id', google_user_id) \
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
        # CORS preflight request - respond with allowed methods and headers
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        return response

    request_json = request.get_json(silent=True)
    token = request.headers.get('Authorization')
    if not token:
        response = jsonify({'error': 'Missing OAuth token'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 401

    # # Remove 'Bearer ' from the token string if present
    if token.startswith('Bearer '):
        token = token[len('Bearer '):]

    # # Verify the token and extract the user's Google ID (sub)
    google_token_info = verify_oauth_token(token)
    if not google_token_info:
        response = jsonify({'error': 'No Google token info.'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 400

    google_user_id = google_token_info.get('sub')
    if not google_user_id:
        response = jsonify({'error': 'Invalid OAuth token'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 401

    # Check if the request has valid data to write
    if request_json and 'note' in request_json and 'timestamp' in request_json:
        note = request_json['note']
        date_time_obj = datetime.fromtimestamp(request_json['timestamp'] / 1000)
    else:
        response = jsonify({'error': 'Missing data to write'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 400

    try:
        ai_response = summarize_note(note)
        note_headline = generate_note_headline(note)
        db.collection('chrome_extension_notes').add(
            {
                'human_note': note,
                'note_headline': note_headline,
                'ai_updated_note': ai_response,
                'date_time': date_time_obj,
                "google_user_id": google_user_id
            })
        live_summary = get_live_summary()
        print(live_summary)
        response = jsonify({'message': live_summary})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 200
    except Exception as e:
        print(f"Error writing to Firestore: {e}")
        response = jsonify({'error': 'Failed to write data to Firestore'})
        response.headers.add('Access-Control-Allow-Origin', 'chrome-extension://cdjhdcbiabimlbcjhdhojcjhedbfeekk')
        return response, 500


def get_live_summary():
    """Returns the summary of what has been going on in your day to day for the past week.
    """

    now = datetime.now()
    formatted_date = now.strftime("%A, %B %d, %Y")
    formatted_time = now.strftime("%I:%M %p")  # Formats time as HH:MM AM/PM
    seven_days_ago = now - timedelta(days=7)

    # Query Firestore collection for documents within the last 7 days, ordered by date_time descending
    notes_ref = db.collection("chrome_extension_notes")
    query = notes_ref.where("date_time", ">=", seven_days_ago)\
                    .where("date_time", "<=", now)\
                    .order_by("date_time", direction='DESCENDING')

    # Execute query and print results
    notes_context = ""
    results = query.stream()
    for doc in results:
        d = doc.to_dict()
        note = f"""
        Date of Note: {d['date_time']}

        Note:
        {d['human_note']}


        """
        notes_context += note

    context_summary = summarize_note(notes_context)
    # Check time of day
    hour = now.hour
    if 4 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    
    return f"""
    *{greeting}*
    It is {formatted_time} on {formatted_date}

    *Live Context Summary:*

    {context_summary}
    """

# if __name__ == '__main__':
#     app.run(debug=True)
