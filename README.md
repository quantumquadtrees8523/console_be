# Deploy Function
gcloud functions deploy write_to_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB


gcloud functions deploy get_from_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated


gcloud functions deploy get_latest_summary \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated

# Testing
functions-framework --target=get_from_firestore --port=8080
functions-framework --target=write_to_firestore --port=8080
functions-framework --target=get_latest_summary --port=8080


# Python Version
pyenv 3.8.12 64-bit ~/.pyenv/versions/3.8.12/bin/python