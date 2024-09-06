def get_most_probable_class_and_percent(model, X):
    # Get class probabilities using predict_proba
    probabilities = model.predict_proba(X)

    # Find the index of the class with the highest probability
    most_probable_class_index = probabilities.argmax(axis=1)

    # Get the corresponding probability for the most probable class
    most_probable_percent = probabilities[
        range(len(probabilities)), most_probable_class_index
    ]

    # Return the most probable class and its probability
    return most_probable_class_index, most_probable_percent * 100


if __name__ == "__main__":
    # Example usage:
    # Assuming 'your_model' is your trained model, and 'your_data' is the data to predict on
    most_probable_class, most_probable_percent = get_most_probable_class_and_percent(
        your_model, your_data
    )

    print(f"Most Probable Class: {most_probable_class}")
    print(f"Probability: {most_probable_percent:.2f}%")
