import os
import nltk
import joblib
from funcs import get_most_probable_class_and_percent
from web_api.log import logger

nltk.download('punkt')

MODEL_FILE = 'moderation_model.joblib'

class ModerationModel:
    def __init__(self, learns=False):
        self.model = self.load_or_train_model()
        self.learns = learns

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
        # Use the trained model to get the most probable class and its probability
        most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])

        # Moderation decision based on the most probable class (0: approved, 1: flagged)
        if percent > 60:
            if most_probable_class == 1:
                self._log_comment(1, comment)
                logger.info("Comment flagged for moderation.")
                logger.debug(f"The certainty of '{comment}' being {most_probable_class} is {percent}%")
                return True
            elif most_probable_class == 0:
                self._log_comment(0, comment)
                logger.info("Comment approved.")
                logger.debug(f"The certainty of '{comment}' being {most_probable_class} is {percent}%")
                return False
            
        else:
            logger.warning("Model uncertainty. Defaulting to approval.")
            logger.debug(f"Model guessed that '{comment}' is {'negative' if most_probable_class == 0 else 'positive'} with certainty {percent}%")
            return False

    def _log_comment(self, label, comment):
        if self.learns:
            filename = f"training/{label}_future.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(comment + '\n')
            logger.debug(f"Added to future training data for label {label}.")

        else:
            logger.debug("Learning has been disabled by config. Won't add comments to future training data.")

if __name__ == "__main__":
    # Example usage from the command prompt
    model_instance = ModerationModel(learns=True)  # Set learns to True if you want to collect future training data
    while True:
        comment_to_moderate = input("Enter the comment to moderate: ")
        model_instance.moderate_comment(comment_to_moderate)
