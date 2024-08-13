import re
import string

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)

    # Remove social media tags (e.g., @username)
    text = re.sub(r'@\w+', '', text)

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Optionally, remove stopwords
    # Example with NLTK:
    # from nltk.corpus import stopwords
    # stop_words = set(stopwords.words('english'))
    # text = ' '.join([word for word in text.split() if word not in stop_words])

    # Stemming or Lemmatization
    # Example with NLTK:
    # from nltk.stem import PorterStemmer
    # stemmer = PorterStemmer()
    # text = ' '.join([stemmer.stem(word) for word in text.split()])

    return text
