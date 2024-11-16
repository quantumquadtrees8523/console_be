# Deploy Function
gcloud functions deploy write_to_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated


gcloud functions deploy get_from_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated


# Testing
functions-framework --target=FUNCTION --port=8080


