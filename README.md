# Deploy Function
gcloud functions deploy write_to_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB


gcloud functions deploy get_from_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB


gcloud functions deploy get_latest_summary \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB

# Testing
functions-framework --target=get_from_firestore --port=8080
functions-framework --target=write_to_firestore --port=8080
functions-framework --target=get_latest_summary --port=8080


# Python Version
pyenv 3.8.12 64-bit ~/.pyenv/versions/3.8.12/bin/python

# TODO: Create Cloud schedulers
gcloud scheduler jobs create http write-to-firestore-keep-warm-job \
    --schedule "*/1 * * * *" \
    --uri "https://us-central1-jarvis-8ce89.cloudfunctions.net/write_to_firestore" \
    --http-method POST
    --location "us-central1"


gcloud scheduler jobs create http get-latest-summary-keep-warm-job \
    --schedule "*/5 * * * *" \
    --uri "https://REGION-PROJECT.cloudfunctions.net/FUNCTION_NAME" \
    --http-method GET


gcloud scheduler jobs create http get-from-firestore-keep-warm-job \
    --schedule "*/5 * * * *" \
    --uri "https://REGION-PROJECT.cloudfunctions.net/FUNCTION_NAME" \
    --http-method GET