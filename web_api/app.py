"""
Webhooks and shit for HaSpDe (Hate speech detection system)
"""

import json
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
from profane_detector import ProfaneDetector
from moderation_model import ModerationModel
from log import logger
import datetime
from config import Config

# Initialization
config = Config()
processed_comments = set()
app = Flask(__name__)

# MongoDB setup
client = MongoClient(config.MONGODB_URI)
db = client[config.DB_NAME]
comments_collection = db["comments"]

# Use configurations from config
INSTAGRAM_ACCESS_TOKEN = config.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_API_VERSION = config.INSTAGRAM_API_VERSION
INSTAGRAM_VERIFY_TOKEN = config.INSTAGRAM_VERIFY_TOKEN
IMPROVE = config.IMPROVE
HUMAN_REVIEW = config.HUMAN_REVIEW
ERROR_STATUS = json.dumps({"status": "error"}), 200

# Load models that we need
moderation_model = ModerationModel(IMPROVE, HUMAN_REVIEW)
profane_detector = ProfaneDetector()


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Handle incoming webhook requests for verification and event processing.

    Returns:
    Response: JSON response based on the request type.
    """
    print("\n=== New Request ===")
    print(f"Request Method: {request.method}")
    print(f"Request Headers: {request.headers}")
    print(f"Request Args: {request.args}")
    print(f"Request Data (raw): {request.data.decode('utf-8')}")

    if request.method == "GET":
        return handle_verification(request)

    elif request.method == "POST":
        return handle_webhook_event(request)

    # If the request method is neither GET nor POST
    return method_not_allowed()


def handle_verification(request):
    """
    Verify the Instagram webhook subscription.

    Parameters:
    request (flask.Request): The incoming request containing verification parameters.

    Returns:
    Response: A plain text response with the challenge code on success or a JSON error message on failure.
    """
    # Extract verification parameters from the request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Verify the subscription request
    if mode == "subscribe" and token == INSTAGRAM_VERIFY_TOKEN:
        print("Verification successful!")
        return challenge, 200  # Return the challenge code for verification

    print("Invalid verification token!")
    return (
        jsonify({"error": "Invalid verification token"}),
        403,
    )  # Return an error response


def handle_webhook_event(request):
    """
    Handle incoming webhook events from Instagram and process comments.

    Parameters:
    request (flask.Request): The incoming request containing webhook data.

    Returns:
    Response: A JSON response indicating the status of the operation.
    """
    # Parse JSON data from the request
    data = request.json
    print("Received webhook data:")
    print(json.dumps(data, indent=2))  # Pretty-print the received data for debugging

    # Validate the structure of the incoming data
    if "entry" not in data or not isinstance(data["entry"], list):
        return ERROR_STATUS

    for entry in data["entry"]:
        if "changes" not in entry or not isinstance(entry["changes"], list):
            return ERROR_STATUS  # Notify the webhook sender of the issue

        for change in entry["changes"]:
            if change.get("field") != "comments" or "value" not in change:
                return ERROR_STATUS  # Notify the webhook sender of the issue

            comment_data = change["value"]
            comment_id = comment_data["id"]
            comment_text = comment_data.get("text", "")
            platform = "instagram"

            # Store comment in MongoDB if it doesn't already exist
            if not comments_collection.find_one({"id": comment_id}):
                comment_to_db(comment_id, comment_text, platform)

            # If human review is disabled, handle the comment
            if not HUMAN_REVIEW:
                handle_comment(comment_data)  # Process comment using HaSpDe

    return jsonify({"status": "ok"}), 200


def comment_to_db(comment_id, comment_text, platform):
    """
    Store a comment in the database.

    Parameters:
    comment_id (str): The unique identifier for the comment.
    comment_text (str): The text content of the comment.
    platform (str): The platform from which the comment originated.
    """
    try:
        # Prepare the comment data for insertion
        comment_data = {
            "id": comment_id,
            "text": comment_text,
            "status": "pending",
            "evaluation": evaluate_comment(comment_text),
            "platform": platform,
        }

        # Insert the comment into the database
        comments_collection.insert_one(comment_data)
        print(f"Comment with ID {comment_id} successfully added to the database.")

    except Exception as e:
        print(f"Error inserting comment with ID {comment_id}: {e}")
        # Optionally, handle the error (e.g., log it or raise an exception)


def handle_comment(comment_data):
    """
    Process an incoming comment for moderation.

    Parameters:
    comment_data (dict): The data of the comment, including its ID and text.
    """
    comment_id = comment_data["id"]
    comment_text = comment_data.get("text", "")

    # Check if the comment has already been processed
    if comment_id not in processed_comments:
        processed_comments.add(comment_id)  # Add the comment ID to the processed set

        # Moderate the comment using the moderation model
        if moderation_model.moderate_comment(comment_text):
            remove(comment_id)  # Remove the comment if it is deemed inappropriate
            print(f"Comment {comment_id} has been removed.")
        else:
            approve(comment_id)  # Approve the comment if it is appropriate
            print(f"Comment {comment_id} has been approved.")
    else:
        print(f"Comment {comment_id} has already been processed.")


@app.route("/review", methods=["GET"])
def review():
    """
    Retrieve and render a pending comment for review.

    Returns:
    Response: Rendered HTML template for comment review or a message indicating no comments are pending.
    """
    # Find a pending comment from the database
    pending_comment = comments_collection.find_one({"status": "pending"})

    if pending_comment:
        comment_id = pending_comment["id"]
        comment_text = pending_comment["text"]
        evaluation_result = pending_comment["evaluation"]

        # Update the status of the comment to 'in_review'
        comments_collection.update_one(
            {"id": comment_id}, {"$set": {"status": "in_review"}}
        )

        return render_template(
            "review.html",
            comment_id=comment_id,
            comment_text=comment_text,
            evaluation_result=evaluation_result,
        )
    else:
        return render_template(
            "nothing_to_review.html"
        )  # Render a template indicating no comments are available for review


@app.route("/skip/<comment_id>", methods=["POST"])
def skip(comment_id):
    # Update the comment status in MongoDB
    comments_collection.update_one({"id": comment_id}, {"$set": {"status": "skipped"}})
    return redirect(url_for("review"))


@app.route("/approve/<comment_id>", methods=["POST"])
def approve(comment_id):
    # Update the comment status in MongoDB
    comment = comments_collection.find_one({"id": comment_id})
    moderation_model._log_comment(comment=comment["text"], label=0)
    comments_collection.update_one({"id": comment_id}, {"$set": {"status": "approved"}})
    return redirect(url_for("review"))


@app.route("/remove/<comment_id>", methods=["POST"])
def remove(comment_id):
    comment = comments_collection.find_one(
        {"id": comment_id}
    )  # Find the comment from database

    comments_collection.update_one(
        {"id": comment_id}, {"$set": {"status": "to_remove"}}
    )  # Let database know, that we will soon remove the comment from the social media platform

    moderation_model._log_comment(
        comment=comment["text"], label=1
    )  # On our AI model, add to training data

    remove_comment(comment_id)

    return redirect(url_for("review"))


def evaluate_comment(comment_text):
    """
    Evaluate the given comment for profanity using the profane_detector model
    designed for HaSpDe.

    Parameters:
    comment_text (str): The text of the comment to evaluate.

    Returns:
    str: "Positive" if no profanity is detected, "Negative" otherwise.
    """
    print(f"Evaluating comment: {comment_text}")

    # Detect profanity in the comment text
    result = profane_detector.detect_api("fi", comment_text)
    print(f"Profane detector result: {result}")

    # Determine evaluation based on detection result
    evaluation = "Negative" if result else "Positive"
    print(f"Evaluation result: {evaluation}")

    return evaluation


import requests


def remove_comment(comment_id):
    """
    Remove a comment from Instagram using the Graph API.

    Parameters:
    comment_id (str): The unique identifier for the comment to be removed.
    """
    # Construct the API endpoint URL
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{comment_id}"
    headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}

    try:
        # Send a DELETE request to remove the comment
        response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            print(f"Comment with ID {comment_id} removed successfully.")
            # Update the comment status in the database
            comments_collection.update_one(
                {"id": comment_id}, {"$set": {"status": "removed"}}
            )
        else:
            print(
                f"Failed to remove comment with ID {comment_id}. Status code: {response.status_code}, Response: {response.text}"
            )

    except requests.RequestException as e:
        print(
            f"An error occurred while trying to remove comment with ID {comment_id}: {e}"
        )


def method_not_allowed():
    print("Method not allowed!")
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT)
