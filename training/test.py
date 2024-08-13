import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from ..moderation_model import ModerationModel


class ModerationModelTest:
    def __init__(self, moderation_model):
        self.model = moderation_model

    def run_tests(self, test_data):
        true_labels = []
        predicted_labels = []

        for comment, label in test_data:
            true_labels.append(label)
            prediction = self.model.moderate_comment(comment)
            # Convert boolean output to integer (True -> 1, False -> 0)
            predicted_labels.append(int(prediction))

        return true_labels, predicted_labels

    def calculate_metrics(self, true_labels, predicted_labels):
        accuracy = accuracy_score(true_labels, predicted_labels)
        precision = precision_score(true_labels, predicted_labels)
        recall = recall_score(true_labels, predicted_labels)
        f1 = f1_score(true_labels, predicted_labels)

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

# Example test data: list of tuples (comment, label) where label is 0 for approved and 1 for flagged
test_data = [
    ("This is a good comment.", 0),
    ("This comment is offensive!", 1),
    ("I love this post.", 0),
    ("You are stupid!", 1),
    ("Great job!", 0),
    ("This is spam.", 1)
]

# Assuming the moderation model is already trained and available as `moderation_model`
moderation_model = ModerationModel(learns=False, human_review=False)  # Set human_review to False for automated testing

# Create test suite instance
test_suite = ModerationModelTest(moderation_model)

# Run tests
true_labels, predicted_labels = test_suite.run_tests(test_data)

# Calculate and print metrics
metrics = test_suite.calculate_metrics(true_labels, predicted_labels)
print("Test Results:")
for metric, value in metrics.items():
    print(f"{metric}: {value:.4f}")
