# moderation_evaluation.py
import os
import joblib
from preprocessing import preprocess_text
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

MODEL_FILE = '../moderation_model.joblib'

def load_model():
    # Load the pre-trained moderation model from the file
    if not os.path.exists(MODEL_FILE):
        print("Error: Moderation model not found. Train a model first.")
        return None

    return joblib.load(MODEL_FILE)

def load_comments(file_path):
    # Load comments from the specified file
    with open(file_path, 'r', encoding="utf-8") as file:
        comments = file.readlines()
    return comments

def fit_new_data_to_model(model, comments, labels):
    # Add new data to the existing training data and retrain the model
    existing_X_train, existing_y_train = load_existing_training_data()
    X_train = existing_X_train + [comment.strip() for comment in comments]
    y_train = existing_y_train + labels

    # Train the updated model
    model = train_updated_model(X_train, y_train)

    return model

def train_updated_model(X_train, y_train):
    # Create a pipeline with a CountVectorizer and a Multinomial Naive Bayes classifier
    updated_model = make_pipeline(CountVectorizer(preprocessor=preprocess_text), MultinomialNB())

    # Train the updated model
    updated_model.fit(X_train, y_train)

    # Save the updated model to a file
    joblib.dump(updated_model, MODEL_FILE)

    return updated_model

def list2str(list_item):
    # Convert a list of items to a space-separated string
    text = " ".join(list_item)
    return text

def load_existing_training_data():
    # Load existing training data from a file
    existing_X_train = []
    existing_y_train = []

    if os.path.exists("existing_training_data.txt"):
        with open("existing_training_data.txt", 'r', encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                things = line.strip().split(',')
                label = things[-1]
                comment = list2str(things[:len(things)-1])
                existing_X_train.append(comment)
                existing_y_train.append(int(label))

    return existing_X_train, existing_y_train

def save_training_data(X_train, y_train):
    # Save the training data to a file
    with open("existing_training_data.txt", 'w', encoding="utf-8") as file:
        for comment, label in zip(X_train, y_train):
            comment = comment.replace("\n", "")
            file.write(f"{comment},{label}\n")

def move_comments(source_path, destination_path):
    # Move comments from source_path to destination_path
    comments = load_comments(source_path)
    with open(destination_path, 'a', encoding="utf-8") as dest_file:
        dest_file.writelines(comments)

    # Clear the source file
    with open(source_path, 'w'):
        pass

if __name__ == "__main__":
    # Load the pre-trained moderation model
    moderation_model = load_model()

    if moderation_model is not None:
        # Load additional data from 0.txt and 1.txt
        comments_0_additional = load_comments("0.txt") + load_comments("0_future.txt")
        comments_1_additional = load_comments("1.txt") + load_comments("1_future.txt")

        # Assign labels (0: approved, 1: flagged)
        labels_0_additional = [0] * len(comments_0_additional)
        labels_1_additional = [1] * len(comments_1_additional)

        # Fit new data to the existing model
        updated_model = fit_new_data_to_model(moderation_model, comments_0_additional + comments_1_additional,
                                              labels_0_additional + labels_1_additional)

        # Save the combined training data
        save_training_data(comments_0_additional + comments_1_additional, labels_0_additional + labels_1_additional)

        # Move evaluated comments from 0_future.txt to 0.txt
        move_comments("0_future.txt", "0.txt")

        # Move evaluated comments from 1_future.txt to 1.txt
        move_comments("1_future.txt", "1.txt")
