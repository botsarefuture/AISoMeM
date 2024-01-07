import os
import nltk
import joblib
import preprocessing 

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
        # Use the trained model to predict moderation
        prediction = self.model.predict([comment])[0]

        # Moderation decision based on the prediction (0: approved, 1: flagged)
        if prediction == 1:
            self._log_comment(1, comment)
            logger.info("Comment flagged for moderation.")
            return True
        elif prediction == 0:
            self._log_comment(0, comment)
            logger.info("Comment approved.")
            return False
        else:
            logger.warning("Model uncertainty. Defaulting to approval.")
            return False

    def _log_comment(self, label, comment):
        if self.learns:
            filename = f"{label}_future.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(comment + '\n')
            logger.debug(f"Added to future training data for label {label}.")

        else:
            logger.debug(f"Learning has been disabled by config. Won't add comments to future training data.")

if __name__ == "__main__":
    # Example usage from the command prompt
    model_instance = ModerationModel(learns=True)  # Set learns to True if you want to collect future training data
    while True:
        comment_to_moderate = input("Enter the comment to moderate: ")
        model_instance.moderate_comment(comment_to_moderate)
