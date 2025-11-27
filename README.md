Fake News Detector — Quick Run Guide

Prerequisites
- Python 3.8+ installed
- Git (optional)

Recommended (Windows PowerShell) steps

1) Create and activate a virtual environment
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2) Install dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3) Train the model (optional if you already have `model/model.pkl` and `model/vectorizer.pkl`)
```powershell
cd training\backend
python train_model.py
```

4) Run the backend web app
```powershell
# from repo root
cd training\backend
python app.py
```

5) Open the frontend
- Open `training/frontend/index.html` in your browser (or use the hosted endpoints if integrating with a frontend dev server).

Notes
- The backend uses SQLite and will create `training/backend/fake_news.db` automatically.
- If you already have trained model files in `training/backend/model/`, skip step 3.
- To run in development mode with debug logging, set environment variable `FLASK_ENV=development` before running `app.py`.

Troubleshooting
- If `train_model.py` fails due to missing packages, ensure `pandas` and `scikit-learn` are installed from `requirements.txt`.
- If you get parser errors with BeautifulSoup, ensure `beautifulsoup4` is installed.

If you'd like, I can also:
- Add a `scripts` folder with convenience run scripts for PowerShell and Bash.
- Pin more specific package versions after you test installs on your environment.
