import pyttsx3
import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
channel_id = "C088S1BNP3Q"
permanent_token = "xoxb-8306856133108-8289836932231-cKVw2VntC7n59vCKOsDpeUn4"
slack_api_url = "https://slack.com/api"
processed_events = set()

def get_bot_user_id(token):
    url = "https://slack.com/api/auth.test"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print(response)
    if response.status_code == 200 and response.json().get("ok"):
        return response.json()["user_id"]
    else:
        raise Exception("Failed to fetch bot user ID")

bot_user_id = get_bot_user_id(permanent_token)

def text_to_speech(text, output_file):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 1)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)
    engine.say(text)
    engine.save_to_file(text, output_file)
    engine.runAndWait()

def fetch_latest_message(channel_id, token):
    url = f"{slack_api_url}/conversations.history"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"channel": channel_id, "limit": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        messages = response.json().get("messages", [])
        if messages:
            return messages[0]["text"]
    return None

def post_message_with_file(channel_id, token, file_path, text="Here's the file:"):
    try:
        file_size = os.path.getsize(file_path)
        upload_url_data = requests.post('https://slack.com/api/files.getUploadURLExternal', {'token': token, 'filename': os.path.basename(file_path), 'length': file_size}).json()

        if not upload_url_data.get('ok'):
            raise Exception(f"Failed to get upload URL: {upload_url_data.get('error')}")

        upload_url = upload_url_data['upload_url']
        file_id = upload_url_data['file_id']

        with open(file_path, 'rb') as f:
            upload_response = requests.post(upload_url, data=f)

        if upload_response.status_code != 200:
            raise Exception(f"File upload failed with status code: {upload_response.status_code}, Response: {upload_response.text}")

        complete_upload_data = requests.post('https://slack.com/api/files.completeUploadExternal',headers={'Authorization': f'Bearer {token}','Content-Type': 'application/json; charset=utf-8'},json={'files': [{'id': file_id, 'title': os.path.basename(file_path)}],'channel_id': channel_id,'initial_comment': text,}).json()

        if not complete_upload_data.get('ok'):
            raise Exception(f"Failed to complete file upload: {complete_upload_data.get('error')}")

        return complete_upload_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    if data.get("event"):
        event = data["event"]
        event_id = data.get("event_id")
        if event_id in processed_events:
            print(f"Duplicate event received: {event_id}, skipping...")
            return jsonify({"status": "duplicate"})

        processed_events.add(event_id)

        if event.get("user") == bot_user_id:
            print("Ignored bot's own message.")
            return jsonify({"status": "ignored"})

        if event["type"] == "message" and not event.get("subtype"):
            message_text = event["text"]
            print(f"New message received: {message_text}")
            output_file = "output.wav"
            text_to_speech(message_text, output_file)
            success = post_message_with_file(channel_id, permanent_token, output_file, message_text)
            if success:
                print("Audio file posted successfully!")
            else:
                print("Failed to post the audio file.")

    return jsonify({"status": "ok"})
if __name__ == "__main__":
    app.run(port=3000)


# MOHSIN APP 
# channel_id = "C089AHH7T25"
# permanent_token = "xoxb-2685567434578-6066987844816-jSbswxkNqsA3oFOP49qKZYiG"
# invite @Voice Bot

# OLD METHOD TO SEND FILE 
# def post_message_with_file(channel_id, token, file_path, text="Here's the audio file:"):
#     slack_api_url = "https://slack.com/api"
#     url = f"{slack_api_url}/files.upload"
#     headers = {"Authorization": f"Bearer {token}"}
#     files = {"file": (file_path, open(file_path, "rb"), "video/mp4")}
#     data = {"channels": channel_id, "initial_comment": "Audio file for the message"+ " " + text}
#     response = requests.post(url, headers=headers, files=files, data=data)
#     print(response.json())
#     return response.status_code == 200, response.json()

