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
functions-framework --target=get_daily_digest --port=8080


# Python Version + Virtual Environment
<!-- pyenv 3.8.12 64-bit ~/.pyenv/versions/3.8.12/bin/python -->
Switched over to python 3.10 using homebrew
python@3.10 3.10.15 -> located at /usr/local/opt/python@3.10
Verify installation version using: `$ /usr/local/opt/python@3.10/bin/python3.10 --version`
Set virtual environment like this: `$ /usr/local/opt/python@3.10/bin/python3.10 -m venv ~/.console_venv`
The default venv for this project will be `~/.console_venv`
Activate by: `$ source ~/.console_venv/bin/activate`

## Python Path
You'll want to set python path in the virtual environment so that everything is viewable. Right now it's being set manually.
There is a world very soon where you should just update the virtual environment startup script.
`$ export PYTHONPATH=/Users/suryaduggirala/projects/console_be:$PYTHONPATH`
