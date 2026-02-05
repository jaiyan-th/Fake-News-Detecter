# Fake News Detector

A comprehensive full-stack machine learning application designed to detect and classify fake news articles. It features real-time analysis, user authentication, history tracking, and an interactive dashboard.

## 🚀 Features

- **Real-time Analysis**: Instant classification of news articles as "REAL" or "FAKE" using a trained Machine Learning model.
- **User Authentication**: Secure Login and Registration system to manage user profiles.
- **History & Dashboard**: Track past analyses and view statistics on your detection activities.
- **Source Credibility**: Automatic scoring of news source domains.
- **Sentiment Analysis**: Analyzes the emotional tone of the article content.
- **Similar Articles**: Finds and displays textually similar articles from the dataset.
- **Trending Topics**: Visualizes common themes in flagged fake news.
- **Admin Interface**: Restricted area for administrative oversight (if configured).

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Machine Learning**: Scikit-Learn (TF-IDF Vectorization, PassiveAggressiveClassifier), Pandas, NumPy
- **Database**: SQLite (managed via Flask)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS (Google Fonts: Google Sans, Outfit, Inter)

## 📂 Project Structure

```
Fake-News-Detecter-main/
├── fake_news_detector/
│   ├── requirements.txt         # Project dependencies
│   └── training/
│       └── backend/
│           ├── app.py           # Main Flask application entry point
│           ├── database.py      # Database models and connection logic
│           ├── train_model.py   # Script to retrain the ML model
│           ├── model/           # Stores trained model.pkl and vectorizer.pkl
│           ├── templates/       # HTML templates for the frontend
│           ├── static/          # CSS, JS, and images
│           └── fake_news.db     # SQLite database (auto-generated)
```

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### 1. Environment Setup

It is recommended to use a virtual environment.

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate
```

### 2. Install Dependencies

Navigate to the inner `fake_news_detector` directory where `requirements.txt` is located.

```powershell
cd fake_news_detector
pip install -r requirements.txt
```

### 3. Run the Application

Navigate to the `backend` directory and start the Flask app.

```powershell
cd training\backend
python app.py
```

The application will start at `http://localhost:5000` (or the port specified in the console).

### 4. Training the Model (Optional)

If you need to retrain the model (e.g., if `model.pkl` is missing or you have new data):

```powershell
cd fake_news_detector\training\backend
python train_model.py
```

## 🔍 Usage

1.  **Register/Login**: Create an account to save your analysis history.
2.  **Home Page**: Paste a news article title or text into the analysis box.
3.  **Analyze**: Click "Analyze Article" to see the prediction (Real/Fake), confidence score, and detailed breakdown.
4.  **Profile**: Visit your profile to change your password and view your activity stats.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.