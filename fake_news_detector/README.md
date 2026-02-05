# Fake News Detector - Core Module

This directory contains the core implementation of the Fake News Detector, including the machine learning model training scripts, the Flask backend, and the dataset.

## 📂 Structure

- **`requirements.txt`**: List of Python dependencies required to run the backend and training scripts.
- **`training/`**: Contains the code for the backend application and model training.
    - **`backend/`**:
        - **`app.py`**: The main Flask application server. Handles routes, API endpoints, and serves the frontend.
        - **`train_model.py`**: A script to retrain the machine learning model using the dataset.
        - **`database.py`**: Handles SQLite database connections and operations.
        - **`model/`**: Directory where the trained `model.pkl` and `vectorizer.pkl` are saved.
        - **`templates/`**: HTML templates for the web interface.
        - **`static/`**: CSS, JavaScript, and other static assets.
    - **`data/`**:
        - **`fake_or_real_news.csv`**: The dataset used for training and testing the model.

## ⚙️ Setup & Usage

### 1. Install Dependencies

Ensure you are in this directory (`fake_news_detector/`) before running the install command:

```powershell
pip install -r requirements.txt
```

### 2. Run the Backend

To start the web application:

```powershell
cd training\backend
python app.py
```

The server usually starts at `http://localhost:5000`.

### 3. Retrain the Model

If you have modified the dataset or want to regenerate the model files:

```powershell
cd training\backend
python train_model.py
```

This will output the accuracy score and save the new model artifacts to the `model/` directory.

## 🧪 Development Notes

-   **Database**: The application uses a SQLite database (`fake_news.db`) which is automatically created in the `training/backend/` directory upon the first run.
-   **Configuration**: Check `app.py` for configuration settings such as secret keys and debug mode.
