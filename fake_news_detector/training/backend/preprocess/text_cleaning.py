import re
import string

def clean_text(text):
    """
    Cleans the input text by performing the following:
    - Lowercasing
    - Removing URLs
    - Removing HTML tags
    - Removing punctuation
    - Removing line breaks
    - Removing words with numbers
    """

    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # remove URLs
    text = re.sub(r'<.*?>', '', text)  # remove HTML tags
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)  # remove punctuation
    text = re.sub(r'\n', '', text)  # remove line breaks
    text = re.sub(r'\w*\d\w*', '', text)  # remove words with numbers
    return text
