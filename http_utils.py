import requests
def post(api_url: str, event_data: dict, bearer_token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    response: requests.Response = requests.post(api_url, json=event_data, headers=headers)
    
    if response.status_code == 200 or response.status_code == 201:
        try:
            # res_json = response.json()
            return response.text
        except Exception as e:
            print("Exception: ", e)
            return ""
    else:
        raise Exception(f"Failed to create event: {response.status_code} - {response.text}")