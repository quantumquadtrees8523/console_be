#!/bin/bash

# Enable verbose mode
set -x

echo "Deploying write_to_firestore function..."
gcloud functions deploy write_to_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB

echo "Deploying get_from_firestore function..."
gcloud functions deploy get_from_firestore \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB

echo "Deploying get_latest_summary function..."
gcloud functions deploy get_latest_summary \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB

echo "Deploying get_daily_digest function..."
gcloud functions deploy get_daily_digest \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GiB

set +x
