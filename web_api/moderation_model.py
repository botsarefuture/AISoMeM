import os
import nltk
import joblib
from log import logger
from profane_detector import ProfaneDetector
from pymongo import MongoClient


nltk.download('punkt')

MODEL_FILE = '../moderation_model.joblib'

# MongoDB setup
client = MongoClient('mongodb://95.216.148.93:27017/')
db = client['comment_moderation']
comments_collection = db['comments']

def get_most_probable_class_and_percent(model, X):
    # Get class probabilities using predict_proba
    probabilities = model.predict_proba(X)

    # Find the index of the class with the highest probability
    most_probable_class_index = probabilities.argmax(axis=1)

    # Get the corresponding probability for the most probable class
    most_probable_percent = probabilities[range(len(probabilities)), most_probable_class_index]

    # Return the most probable class and its probability
    return most_probable_class_index, most_probable_percent * 100

class ModerationModel:
    def __init__(self, learns=True, human_review=False, strict_anti_profane=False, certainty_needed=80):
        self.model = self.load_or_train_model()
        self.learns = learns
        self.human_review = human_review
        self.profane_detector = ProfaneDetector()
        self.strict_anti_profane = strict_anti_profane
        self.certainty_needed = certainty_needed

    def load_or_train_model(self):
        if os.path.exists(MODEL_FILE):
            # Load the existing model
            model = joblib.load(MODEL_FILE)
            logger.debug("Existing model loaded.")
        else:
            # Train a new model
            logger.error("Train the model first.")
            exit()

        return model

    def moderate_comment(self, comment):
        # First, check if the comment is flagged by the profane detector
        if self.strict_anti_profane:
            is_profane = self.profane_detector.detect_api(None, comment)

        # Ask for feedback before taking action
        if self.human_review:
            feedback = self.ask_for_human_review(comment)
            if feedback in [0, 1]:
                self._log_comment(feedback, comment)
                
                if feedback == 0:
                    logger.info(f'Comment "{comment}" approved based on human review.')
                    return False

                if feedback == 1:
                    logger.info(f'Comment "{comment}" flagged for moderation based on human review.')
                    return True
                
            else:
                logger.warning("Invalid human review input. Defaulting to model prediction.")
                if self.strict_anti_profane:
                    return is_profane

        # If human review is disabled, proceed with automated moderation
        if self.strict_anti_profane and is_profane:
            self._log_comment(1, comment)
            logger.info(f'Comment "{comment}" flagged for moderation due to profanity.')
            return True

        # Use the trained model to get the most probable class and its probability
        most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])

        # Log and return based on model prediction
        
        # We're not doing some random stuff
        if percent >= self.certainty_needed:
            if most_probable_class == 1:
                self._log_comment(1, comment)
                logger.info("Comment flagged for moderation.")
                return True
            elif most_probable_class == 0:
                self._log_comment(0, comment)
                logger.info("Comment approved.")
                return False
        else:
            logger.warning("Model uncertainty. Sending in for human review.")
            self._human_review_db(most_probable_class, percent, comment)
            return False

    def _human_review_db(self, most_probable_class, percent, comment):
        comment_real = comments_collection.find_one({'status': 'pending', 'comment': comment})

        if comment_real:
            comment_id = comment_real["id"]
            comment_text = comment
            
        
        comments_collection.insert_one({
                    'id': comment_id,
                    'text': comment_text,
                    'status': 'pending',
                    'evaluation': "positive" if most_probable_class == 0 else 'negative',
                    'platform': 'HaSpDe'
                })

    def _log_comment(self, label, comment):
        if self.learns:
            filename = f"../training/{label}_future.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(comment + '\n')
            logger.debug(f"Added to future training data for label {label}.")
        else:
            logger.debug("Learning has been disabled by config. Won't add comments to future training data.")

    def ask_for_human_review(self, comment):
        while True:
            try:
                # Use the trained model to get the most probable class and its probability
                most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])

                # Show model results to the human reviewer
                print(f"\nModel prediction:\n- Class: {most_probable_class}\n- Probability: {percent}%\n")

                # Ask human for input
                human_input = int(input(f"Review the comment: '{comment}'\nEnter 1 to flag or 0 to approve: "))
                if human_input in [0, 1]:
                    return human_input
                else:
                    logger.warning("Invalid input. Please enter 1 or 0.")
            except ValueError:
                logger.warning("Invalid input. Please enter 1 or 0.")

if __name__ == "__main__":
    # Example usage from the command prompt
    model_instance = ModerationModel(learns=True, human_review=True)  # Set learns to True if you want to collect future training data
    while True:
        comment_to_moderate = input("Enter the comment to moderate (type 'exit' to quit): ")
        if comment_to_moderate.lower() == 'exit':
            break
        model_instance.moderate_comment(comment_to_moderate)
