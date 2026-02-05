import pandas as pd
import string
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from preprocess.text_cleaning import clean_text

# Ensure the model directory exists
os.makedirs('model', exist_ok=True)

# Load dataset using relative path
print("Loading dataset...")
try:
    df = pd.read_csv('../data/fake_or_real_news.csv')
except FileNotFoundError:
    print("Error: Dataset not found. Please ensure 'fake_or_real_news.csv' is in 'fake_news_detector/training/data/'")
    exit(1)

# Clean the text
print("Cleaning text data...")
df['cleaned_text'] = df['text'].apply(clean_text)

# Split into train/test sets
print("Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(df['cleaned_text'], df['label'], test_size=0.2, random_state=42)

# Vectorize text with bi-rams for better context
print("Vectorizing...")
vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train model - PassiveAggressiveClassifier is standard for fake news
print("Training PassiveAggressiveClassifier...")
model = PassiveAggressiveClassifier(max_iter=50)
model.fit(X_train_vec, y_train)

# Evaluate
y_pred = model.predict(X_test_vec)
score = accuracy_score(y_test, y_pred)
print(f"✅ Accuracy: {score*100:.2f}%")
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred, labels=['FAKE', 'REAL']))

# Save model and vectorizer
print("Saving model artifacts...")
with open('model/model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('model/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print("✅ Model and vectorizer saved successfully to 'model/' directory")
