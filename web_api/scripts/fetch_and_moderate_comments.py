import os
import requests
from moderation_model import ModerationModel  # Import your moderation model class here

REMOVE = False  # Global variable to determine if comments should be removed

def fetch_comments(api_url):
    """
    Fetch comments from the Facebook Graph API.

    Parameters:
    api_url (str): The URL to fetch comments from.

    Returns:
    list: A list of comments fetched from the API.
    """
    comments = []
    try:
        while True:
            response = requests.get(api_url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            if 'data' in data:
                comments.extend(data['data'])
            
            # Check if there's a next page
            if 'paging' in data and 'next' in data['paging']:
                api_url = data['paging']['next']
            else:
                break
    except requests.RequestException as e:
        print(f"Error fetching comments: {e}")
    
    return comments

def remove_comment(comment_id, access_token):
    """
    Remove a comment using the Facebook Graph API.

    Parameters:
    comment_id (str): The ID of the comment to be removed.
    access_token (str): The access token for the Facebook Graph API.
    """
    url = f"https://graph.facebook.com/v20.0/{comment_id}"
    params = {'access_token': access_token}

    try:
        response = requests.delete(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses

        print(f"Comment with ID {comment_id} removed successfully.")
    except requests.RequestException as e:
        print(f"Failed to remove comment with ID {comment_id}: {e}")

if __name__ == "__main__":
    # Example usage
    model_instance = ModerationModel(learns=True, human_review=True)  # Adjust parameters based on your needs

    # Replace with your actual API URL (without the access token for security)
    api_url = "https://graph.facebook.com/v20.0/18236196865259048/comments?access_token=YOUR_ACCESS_TOKEN"

    comments = fetch_comments(api_url)  # Fetch comments from the specified API URL

    for comment_data in comments:
        comment_text = comment_data.get('message', '')  # Updated key for comment text
        comment_id = comment_data.get('id', '')

        if comment_text:
            print(f"Moderating comment: {comment_text}")
            # Use the moderation model to evaluate whether the comment is acceptable
            if model_instance.moderate_comment(comment_text):                
                if REMOVE:
                    remove_comment(comment_id, access_token="YOUR_ACCESS_TOKEN")  # Use a secure method to handle tokens
                print("Removed if chosen to")
