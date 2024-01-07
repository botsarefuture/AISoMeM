import os
import nltk
import joblib
import logging
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import requests
from flask import Flask, request

from moderation_model import ModerationModel
from log import logger

IMPROVE = True

moderation_model = ModerationModel(IMPROVE)

app = Flask("AISoMeM web API")

# Replace these values with your actual values
VERIFY_TOKEN = "your_verify_token"

# Endpoint to handle Meta Webhook events
@app.route('/', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return handle_event_notification(request)
    else:
        return 'Method Not Allowed', 405

def verify_webhook(request):
    hub_mode = request.args.get('hub.mode')
    hub_challenge = request.args.get('hub.challenge')
    hub_verify_token = request.args.get('hub.verify_token')

    if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge
    else:
        return 'Verification Failed', 403

def handle_event_notification(request):
    event = request.json
    entry = event.get("entry")[0]
    changes = entry.get("changes")[0]
    field = changes.get("field")
    value = changes.get("value")
    item = value.get("item")

    if item == "comment":
        sender_info = value.get("from")
        sender_id = sender_info.get("id")
        sender_name = sender_info.get("name")

        message = value.get("message")
        comment_id = value.get("comment_id")
        verb = value.get("verb")

        if verb == "add":
            if moderation_model.moderate_comment(message):
                logger.info(f"Remove comment from {sender_name} (ID: {sender_id}): {message}")
                # Add your code here to hide the comment using the Facebook API
            else:
                logger.info(f"Don't remove comment from {sender_name} (ID: {sender_id}): {message}")

    elif item == "reaction":
        sender_info = value.get("from")
        sender_id = sender_info.get("id")
        sender_name = sender_info.get("name")

        logger.info(f"{sender_name} reacted {value.get('reaction_type')} to {value.get('post_id')}")

    else:
        print(item)
        print(value)

    return ''

if __name__ == '__main__':
    app.run()
