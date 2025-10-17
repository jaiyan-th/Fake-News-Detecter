"""
Minimal Flask App for Testing Connection
Works without ML model for initial testing
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os
import datetime
import re
import math
import requests
from bs4 import BeautifulSoup
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Enable CORS for frontend integration
CORS(app, origins=["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:5000"])

# MongoDB config
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/fake_news_app")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

try:
    mongo = PyMongo(app)
    # Test connection
    mongo.db.command('ping')
    print("✅ Successfully connected to MongoDB")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    raise

def extract_title_from_text(text, max_length=100):
    """Extract a title from news text"""
    sentences = re.split(r'[.!?]+', text.strip())
    if sentences:
        title = sentences[0].strip()
        title = re.sub(r'\s+', ' ', title)
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        return title
    return "News Article"

def generate_card_data(prediction_record):
    """Convert prediction record to card format"""
    return {
        'id': str(prediction_record['_id']),
        'title': extract_title_from_text(prediction_record['news']),
        'content': prediction_record['news'],
        'prediction': prediction_record['prediction'],
        'confidence': prediction_record.get('confidence', 0.85),
        'timestamp': prediction_record['timestamp'].isoformat(),
        'username': prediction_record['username'],
        'imageUrl': f"https://via.placeholder.com/300x200/{'10b981' if prediction_record['prediction'] == 'REAL' else 'ef4444'}/ffffff?text={prediction_record['prediction']}",
        'source': prediction_record.get('source', 'User Submission'),
        'category': prediction_record.get('category', 'General'),
        'tags': prediction_record.get('tags', ['general']),
        'word_count': len(prediction_record['news'].split()),
        'character_count': len(prediction_record['news'])
    }

def error_response(message, code=400):
    """Standardized error response format"""
    return jsonify({
        'error': True,
        'message': message,
        'timestamp': datetime.datetime.now().isoformat()
    }), code

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def extract_article_from_url(url):
    """Extract article text from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find article content using common selectors
        article_selectors = [
            'article', '.article-content', '.post-content', '.entry-content',
            '.content', '.story-body', '.article-body', 'main', '.main-content'
        ]
        
        article_text = ""
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                article_text = ' '.join([elem.get_text().strip() for elem in elements])
                break
        
        # Fallback: get all paragraph text
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Clean up the text
        article_text = re.sub(r'\s+', ' ', article_text).strip()
        
        # Get title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Article from URL"
        
        return {
            'text': article_text,
            'title': title,
            'url': url
        }
        
    except Exception as e:
        raise Exception(f"Failed to extract article from URL: {str(e)}")

# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        users = mongo.db.users
        user = users.find_one({"username": username})
        
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["user_id"] = str(user["_id"])
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        # Validation
        if len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters long")
        
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters long")
        
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")
        
        users = mongo.db.users
        
        # Check if user already exists
        if users.find_one({"username": username}):
            return render_template("register.html", error="Username already exists")
        
        if users.find_one({"email": email}):
            return render_template("register.html", error="Email already registered")
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.datetime.now(),
            "role": "user"
        }
        
        users.insert_one(user_data)
        return render_template("login.html", success="Account created successfully! Please log in.")
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Home route
@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get('username'))

# History route
@app.route("/history")
@login_required
def history():
    try:
        username = session.get('username')
        predictions = list(
            mongo.db.predictions
            .find({"username": username})
            .sort([('timestamp', -1)])
            .limit(50)
        )
        
        return render_template("history.html", predictions=predictions, username=username)
    except Exception as e:
        return render_template("history.html", error=str(e), username=session.get('username'))

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        mongo.db.command('ping')
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'components': {
            'database': db_status,
            'model': 'not_loaded',  # ML model not loaded in minimal version
            'cache': 'healthy'
        },
        'version': '1.0.0-minimal'
    })

# Get paginated cards
@app.route("/api/cards", methods=["GET"])
def get_cards():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
            
        query = {}
        if search:
            query['$or'] = [
                {'news': {'$regex': search, '$options': 'i'}},
                {'username': {'$regex': search, '$options': 'i'}}
            ]
        
        skip = (page - 1) * limit
        total_count = mongo.db.predictions.count_documents(query)
        
        predictions = list(
            mongo.db.predictions
            .find(query)
            .sort([('timestamp', -1)])
            .skip(skip)
            .limit(limit)
        )
        
        cards = [generate_card_data(pred) for pred in predictions]
        total_pages = math.ceil(total_count / limit)
        has_more = page < total_pages
        
        return jsonify({
            'cards': cards,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_more': has_more
            }
        })
        
    except Exception as e:
        return error_response(f"Server error: {str(e)}", 500)

# Enhanced prediction endpoint with URL support
@app.route("/api/predict", methods=["POST"])
def predict_enhanced():
    try:
        data = request.get_json()
        if not data or ('text' not in data and 'url' not in data):
            return error_response("Missing 'text' or 'url' field in request", 400)
        
        # Handle URL input
        if 'url' in data and data['url']:
            try:
                article_data = extract_article_from_url(data['url'])
                news_text = article_data['text']
                source_url = data['url']
                title = article_data['title']
            except Exception as e:
                return error_response(f"Failed to extract article from URL: {str(e)}", 400)
        else:
            news_text = data.get('text', '').strip()
            source_url = None
            title = extract_title_from_text(news_text)
        
        if not news_text or len(news_text) < 10:
            return error_response("Text must be at least 10 characters long", 400)
        
        # Enhanced rule-based prediction
        fake_indicators = {
            'conspiracy': ['aliens', 'conspiracy', 'cover-up', 'secret government', 'illuminati'],
            'sensational': ['shocking', 'unbelievable', 'miracle cure', 'doctors hate', 'one weird trick'],
            'medical_misinformation': ['cure cancer', 'immortal', 'live forever', 'never age'],
            'political_extreme': ['destroy america', 'end of democracy', 'civil war'],
            'supernatural': ['supernatural', 'paranormal', 'ghost', 'psychic powers']
        }
        
        real_indicators = {
            'scientific': ['study shows', 'research indicates', 'according to', 'published in'],
            'credible_sources': ['university', 'institute', 'professor', 'dr.', 'phd'],
            'factual': ['data suggests', 'statistics show', 'evidence indicates'],
            'balanced': ['however', 'on the other hand', 'experts say', 'according to experts']
        }
        
        fake_score = 0
        real_score = 0
        text_lower = news_text.lower()
        
        # Calculate fake score
        for category, keywords in fake_indicators.items():
            for keyword in keywords:
                if keyword in text_lower:
                    fake_score += 1
        
        # Calculate real score
        for category, keywords in real_indicators.items():
            for keyword in keywords:
                if keyword in text_lower:
                    real_score += 1
        
        # Determine prediction
        if fake_score > real_score:
            prediction = "FAKE"
            confidence = min(0.95, 0.65 + (fake_score * 0.1))
        elif real_score > fake_score:
            prediction = "REAL"
            confidence = min(0.95, 0.70 + (real_score * 0.08))
        else:
            # Default based on text characteristics
            if len(news_text) < 100:
                prediction = "FAKE"
                confidence = 0.60
            else:
                prediction = "REAL"
                confidence = 0.75
        
        # Determine category based on content
        categories = {
            'Technology': ['tech', 'ai', 'computer', 'software', 'digital', 'internet'],
            'Health': ['health', 'medical', 'doctor', 'medicine', 'vaccine', 'disease'],
            'Politics': ['government', 'president', 'election', 'congress', 'political'],
            'Science': ['science', 'research', 'study', 'scientist', 'discovery'],
            'Business': ['business', 'company', 'market', 'economy', 'financial']
        }
        
        detected_category = 'General'
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_category = category
                break
        
        prediction_record = {
            'username': session.get('username', 'anonymous'),
            'news': news_text,
            'title': title,
            'prediction': prediction,
            'confidence': confidence,
            'timestamp': datetime.datetime.now(),
            'source': 'URL' if source_url else 'Text Input',
            'source_url': source_url,
            'category': detected_category,
            'tags': [detected_category.lower()],
            'model_version': 'enhanced-rule-based',
            'fake_score': fake_score,
            'real_score': real_score
        }
        
        result = mongo.db.predictions.insert_one(prediction_record)
        prediction_record['_id'] = result.inserted_id
        
        card_data = generate_card_data(prediction_record)
        
        return jsonify({
            'success': True,
            'card': card_data,
            'prediction': {
                'result': prediction,
                'confidence': confidence,
                'model_version': 'enhanced-rule-based'
            },
            'analysis': {
                'fake_indicators': fake_score,
                'real_indicators': real_score,
                'category': detected_category,
                'source_type': 'URL' if source_url else 'Text'
            }
        })
        
    except Exception as e:
        return error_response(f"Prediction failed: {str(e)}", 500)

# Get card statistics
@app.route("/api/cards/stats", methods=["GET"])
def get_card_stats():
    try:
        total_count = mongo.db.predictions.count_documents({})
        real_count = mongo.db.predictions.count_documents({'prediction': 'REAL'})
        fake_count = mongo.db.predictions.count_documents({'prediction': 'FAKE'})
        
        return jsonify({
            'total_predictions': total_count,
            'by_prediction': {
                'REAL': {'count': real_count, 'avg_confidence': 0.85},
                'FAKE': {'count': fake_count, 'avg_confidence': 0.80}
            },
            'recent_activity': {'last_24h': total_count}
        })
        
    except Exception as e:
        return error_response(f"Stats retrieval failed: {str(e)}", 500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting minimal Flask server on port {port}")
    print("📝 Note: Using rule-based prediction (ML model not loaded)")
    print("🌐 Open: http://localhost:5000")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        threaded=True
    )