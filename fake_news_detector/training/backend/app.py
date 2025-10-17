from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
from flask_pymongo import PyMongo
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import pickle
import os
import datetime
import re
import math
import hashlib
import time
from functools import wraps
import logging
from collections import defaultdict
import threading

# Text preprocessing
from preprocess.text_cleaning import clean_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage = defaultdict(list)
rate_limit_lock = threading.Lock()

# Load model and vectorizer
with open(os.path.join("model", "model.pkl"), "rb") as f:
    model = pickle.load(f)

with open(os.path.join("model", "vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

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
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Cache for frequently accessed data
cache = {
    'stats': {'data': None, 'timestamp': 0, 'ttl': 300},  # 5 minutes TTL
    'recent_cards': {'data': None, 'timestamp': 0, 'ttl': 60}  # 1 minute TTL
}

# Utility functions for card data processing
def extract_title_from_text(text, max_length=100):
    """Extract a title from news text"""
    # Split into sentences
    sentences = re.split(r'[.!?]+', text.strip())
    if sentences:
        title = sentences[0].strip()
        # Clean up and truncate
        title = re.sub(r'\s+', ' ', title)
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        return title
    return "News Article"

def generate_card_data(prediction_record):
    """Convert prediction record to card format"""
    news_text = prediction_record['news']
    
    return {
        'id': str(prediction_record['_id']),
        'title': extract_title_from_text(news_text),
        'content': news_text,
        'prediction': prediction_record['prediction'],
        'confidence': prediction_record.get('confidence', 0.85),
        'timestamp': prediction_record['timestamp'].isoformat(),
        'username': prediction_record['username'],
        'imageUrl': generate_placeholder_image_url(prediction_record['prediction']),
        'source': prediction_record.get('source', 'User Submission'),
        'category': prediction_record.get('category', 'General'),
        'tags': prediction_record.get('tags', enhanced_extract_tags_from_text(news_text)),
        'language': prediction_record.get('language', detect_language(news_text)),
        'word_count': len(news_text.split()),
        'character_count': len(news_text),
        'content_hash': prediction_record.get('content_hash', generate_content_hash(news_text)),
        'entities': prediction_record.get('entities', extract_entities(news_text)),
        'model_version': prediction_record.get('model_version', '1.0')
    }

def generate_placeholder_image_url(prediction):
    """Generate placeholder image URL based on prediction"""
    color = "10b981" if prediction == "REAL" else "ef4444"
    return f"https://via.placeholder.com/300x200/{color}/ffffff?text={prediction}"

def extract_tags_from_text(text, max_tags=3):
    """Extract relevant tags from news text"""
    # Simple keyword extraction
    keywords = ['politics', 'health', 'technology', 'sports', 'business', 'entertainment', 'science']
    text_lower = text.lower()
    found_tags = [tag for tag in keywords if tag in text_lower]
    return found_tags[:max_tags]

def error_response(message, code=400):
    """Standardized error response format"""
    logger.warning(f"Error response: {message} (Code: {code})")
    return jsonify({
        'error': True,
        'message': message,
        'timestamp': datetime.datetime.now().isoformat(),
        'code': code
    }), code

def success_response(data, message="Success"):
    """Standardized success response format"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.datetime.now().isoformat()
    })

def rate_limit(max_requests=60, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            
            with rate_limit_lock:
                # Clean old requests
                rate_limit_storage[client_ip] = [
                    req_time for req_time in rate_limit_storage[client_ip]
                    if current_time - req_time < window
                ]
                
                # Check rate limit
                if len(rate_limit_storage[client_ip]) >= max_requests:
                    return error_response(
                        f"Rate limit exceeded. Max {max_requests} requests per {window} seconds.",
                        429
                    )
                
                # Add current request
                rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json_input(required_fields=None):
    """Validate JSON input decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return error_response("Content-Type must be application/json", 400)
            
            data = request.get_json()
            if not data:
                return error_response("Invalid JSON data", 400)
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
            
            g.json_data = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_cached_data(cache_key):
    """Get data from cache if valid"""
    cache_entry = cache.get(cache_key)
    if cache_entry and cache_entry['data'] is not None:
        if time.time() - cache_entry['timestamp'] < cache_entry['ttl']:
            return cache_entry['data']
    return None

def set_cached_data(cache_key, data):
    """Set data in cache"""
    if cache_key in cache:
        cache[cache_key]['data'] = data
        cache[cache_key]['timestamp'] = time.time()

def generate_content_hash(text):
    """Generate hash for content deduplication"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def detect_language(text):
    """Simple language detection"""
    # Basic English detection - can be enhanced with proper language detection library
    english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    words = text.lower().split()[:50]  # Check first 50 words
    english_count = sum(1 for word in words if word in english_words)
    return 'en' if english_count > len(words) * 0.1 else 'unknown'

def extract_entities(text):
    """Extract named entities from text (simplified)"""
    # Simple entity extraction - can be enhanced with NLP libraries
    entities = {
        'persons': [],
        'organizations': [],
        'locations': []
    }
    
    # Basic patterns for entity detection
    person_patterns = [r'\b[A-Z][a-z]+ [A-Z][a-z]+\b']
    org_patterns = [r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Organization)\b']
    location_patterns = [r'\b(?:New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose)\b']
    
    for pattern in person_patterns:
        entities['persons'].extend(re.findall(pattern, text))
    
    for pattern in org_patterns:
        entities['organizations'].extend(re.findall(pattern, text))
    
    for pattern in location_patterns:
        entities['locations'].extend(re.findall(pattern, text))
    
    return entities

def enhanced_extract_tags_from_text(text, max_tags=5):
    """Enhanced tag extraction with more categories"""
    categories = {
        'politics': ['election', 'government', 'president', 'congress', 'senate', 'vote', 'policy', 'democrat', 'republican'],
        'health': ['doctor', 'hospital', 'medicine', 'vaccine', 'virus', 'disease', 'treatment', 'medical', 'covid'],
        'technology': ['computer', 'software', 'internet', 'ai', 'artificial intelligence', 'robot', 'tech', 'digital'],
        'sports': ['football', 'basketball', 'baseball', 'soccer', 'game', 'team', 'player', 'championship', 'olympic'],
        'business': ['company', 'market', 'stock', 'economy', 'finance', 'investment', 'profit', 'business', 'corporate'],
        'entertainment': ['movie', 'music', 'celebrity', 'actor', 'singer', 'film', 'show', 'entertainment', 'hollywood'],
        'science': ['research', 'study', 'scientist', 'discovery', 'experiment', 'university', 'academic', 'journal'],
        'environment': ['climate', 'environment', 'pollution', 'green', 'renewable', 'carbon', 'sustainability'],
        'crime': ['police', 'arrest', 'crime', 'criminal', 'court', 'judge', 'law', 'legal', 'investigation'],
        'international': ['country', 'nation', 'international', 'global', 'world', 'foreign', 'embassy', 'diplomatic']
    }
    
    text_lower = text.lower()
    found_tags = []
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            found_tags.append(category)
    
    return found_tags[:max_tags]

# Import fallback handler
from fallback_handler import render_fallback_page, should_use_fallback

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route("/")
@login_required
def home():
    # Check if we should use fallback interface
    if should_use_fallback(request):
        # Get recent history for fallback users
        try:
            recent_predictions = list(
                mongo.db.predictions
                .find()
                .sort([('timestamp', -1)])
                .limit(10)
            )
            return render_fallback_page(history=recent_predictions)
        except:
            return render_fallback_page()
    
    return render_template("index.html", username=session.get('username'))

# Fallback prediction endpoint for non-JS users
@app.route("/predict_fallback", methods=["POST"])
def predict_fallback():
    try:
        news_text = request.form.get('news', '').strip()
        
        if not news_text:
            return render_fallback_page(error="Please enter some news text")
        
        # Process prediction
        cleaned = clean_text(news_text)
        transformed = vectorizer.transform([cleaned])
        prediction = model.predict(transformed)[0]
        
        # Get confidence score
        try:
            confidence_scores = model.predict_proba(transformed)[0]
            confidence = float(max(confidence_scores))
        except:
            confidence = 0.85
        
        # Save to database
        prediction_record = {
            'username': session.get('username', 'anonymous'),
            'news': news_text,
            'prediction': prediction,
            'confidence': confidence,
            'timestamp': datetime.datetime.now(),
            'source': 'Fallback Interface',
            'model_version': '1.0'
        }
        
        mongo.db.predictions.insert_one(prediction_record)
        
        # Get recent history
        recent_predictions = list(
            mongo.db.predictions
            .find()
            .sort([('timestamp', -1)])
            .limit(10)
        )
        
        return render_fallback_page(
            prediction=prediction,
            confidence=confidence * 100,
            history=recent_predictions
        )
        
    except Exception as e:
        return render_fallback_page(error=f"Analysis failed: {str(e)}")

# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            return render_template("login.html", error="Please enter both username and password")
        
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
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        # Validation
        if not username:
            return render_template("register.html", error="Username is required")
        
        if not email:
            return render_template("register.html", error="Email is required")
        
        if not password:
            return render_template("register.html", error="Password is required")
        
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

# Predict
@app.route("/predict", methods=["POST"])
def predict():
    if "username" not in session:
        return redirect(url_for("login"))

    news = request.form.get("news", "").strip()
    
    if not news:
        return render_template("index.html", error="Please enter some news text to analyze")
    
    try:
        cleaned = clean_text(news)
        transformed = vectorizer.transform([cleaned])
        prediction = model.predict(transformed)[0]
        result = "FAKE" if prediction == "FAKE" else "REAL"

        # Get confidence score
        try:
            confidence_scores = model.predict_proba(transformed)[0]
            confidence = float(max(confidence_scores))
        except:
            confidence = 0.85  # Default confidence if model doesn't support predict_proba

        mongo.db.predictions.insert_one({
            "username": session["username"],
            "news": news,
            "prediction": result,
            "confidence": confidence,
            "timestamp": datetime.datetime.now(),
            "source": "Web Interface",
            "model_version": "1.0"
        })

        return render_template("index.html", prediction=result, news=news, confidence=confidence)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return render_template("index.html", error=f"Analysis failed: {str(e)}")

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

# Clear History
@app.route("/clear_history", methods=["POST"])
def clear_history():
    if "username" not in session:
        return redirect(url_for("login"))

    mongo.db.predictions.delete_many({"username": session["username"]})
    return redirect(url_for("history"))

# Admin View (restricted)
@app.route("/admin")
def admin():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if session["username"] != "admin":
        return "Access denied. Admins only."

    records = list(mongo.db.predictions.find().sort("timestamp", -1))
    return render_template("admin.html", records=records)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Debug route
@app.route("/debug")
def debug():
    with open("../../debug_dashboard.html", "r") as f:
        return f.read()

# Enhanced interface route (force enhanced)
@app.route("/enhanced")
@login_required
def enhanced():
    return render_template("index.html", username=session.get('username'))

# Test dashboard route
@app.route("/test")
def test_dashboard():
    with open("../../test_dashboard.html", "r") as f:
        return f.read()

# ============================================================================
# NEW API ENDPOINTS FOR CARD GRID
# ============================================================================

# Get paginated cards
@app.route("/api/cards", methods=["GET"])
def get_cards():
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        filter_prediction = request.args.get('filter', '').upper()
        sort_by = request.args.get('sort', 'timestamp')
        sort_order = request.args.get('order', 'desc')
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
            
        # Build query
        query = {}
        
        # Add search filter
        if search:
            query['$or'] = [
                {'news': {'$regex': search, '$options': 'i'}},
                {'username': {'$regex': search, '$options': 'i'}}
            ]
        
        # Add prediction filter
        if filter_prediction in ['REAL', 'FAKE']:
            query['prediction'] = filter_prediction
        
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Build sort criteria
        sort_direction = -1 if sort_order == 'desc' else 1
        sort_criteria = [(sort_by, sort_direction)]
        
        # Get total count for pagination
        total_count = mongo.db.predictions.count_documents(query)
        
        # Get paginated results
        predictions = list(
            mongo.db.predictions
            .find(query)
            .sort(sort_criteria)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert to card format
        cards = [generate_card_data(pred) for pred in predictions]
        
        # Calculate pagination info
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
            },
            'filters': {
                'search': search,
                'prediction': filter_prediction,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })
        
    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        return error_response(f"Server error: {str(e)}", 500)

# Get single card details
@app.route("/api/cards/<card_id>", methods=["GET"])
def get_card_details(card_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(card_id):
            return error_response("Invalid card ID", 400)
        
        # Find the prediction record
        prediction = mongo.db.predictions.find_one({'_id': ObjectId(card_id)})
        
        if not prediction:
            return error_response("Card not found", 404)
        
        # Convert to detailed card format
        card_data = generate_card_data(prediction)
        
        # Add additional details for modal view
        card_data.update({
            'full_content': prediction['news'],
            'word_count': len(prediction['news'].split()),
            'character_count': len(prediction['news']),
            'analysis': {
                'prediction': prediction['prediction'],
                'confidence': prediction.get('confidence', 0.85),
                'model_version': '1.0',
                'processed_at': prediction['timestamp'].isoformat()
            }
        })
        
        return jsonify(card_data)
        
    except Exception as e:
        return error_response(f"Server error: {str(e)}", 500)

# Get user's history
@app.route("/api/history", methods=["GET"])
def get_user_history():
    try:
        # Check if user is logged in
        if 'username' not in session:
            return error_response("Authentication required", 401)
        
        username = session['username']
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 50:
            limit = 10
            
        # Build query for user's predictions only
        query = {'username': username}
        
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Get total count for pagination
        total_count = mongo.db.predictions.count_documents(query)
        
        # Get paginated results
        predictions = list(
            mongo.db.predictions
            .find(query)
            .sort([('timestamp', -1)])
            .skip(skip)
            .limit(limit)
        )
        
        # Convert to card format
        cards = [generate_card_data(pred) for pred in predictions]
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit)
        has_more = page < total_pages
        
        # Calculate statistics
        stats = {
            'total': total_count,
            'real_count': mongo.db.predictions.count_documents({**query, 'prediction': 'REAL'}),
            'fake_count': mongo.db.predictions.count_documents({**query, 'prediction': 'FAKE'}),
        }
        
        # Calculate average confidence
        if predictions:
            avg_confidence = sum(pred.get('confidence', 0.85) for pred in predictions) / len(predictions)
            stats['avg_confidence'] = avg_confidence
        else:
            stats['avg_confidence'] = 0
        
        return jsonify({
            'cards': cards,
            'stats': stats,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_more': has_more
            }
        })
        
    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        return error_response(f"Server error: {str(e)}", 500)

# Enhanced prediction endpoint with card format
@app.route("/api/predict", methods=["POST"])
@rate_limit(max_requests=30, window=60)  # 30 requests per minute
@validate_json_input(required_fields=['text'])
def predict_enhanced():
    try:
        data = g.json_data
        news_text = data['text'].strip()
        
        # Validate text length
        if len(news_text) < 10:
            return error_response("Text must be at least 10 characters long", 400)
        
        if len(news_text) > 10000:
            return error_response("Text must be less than 10,000 characters", 400)
        
        # Check for duplicate content
        content_hash = generate_content_hash(news_text)
        existing_prediction = mongo.db.predictions.find_one({'content_hash': content_hash})
        
        if existing_prediction:
            logger.info(f"Returning cached prediction for hash: {content_hash}")
            card_data = generate_card_data(existing_prediction)
            return jsonify({
                'success': True,
                'card': card_data,
                'prediction': {
                    'result': existing_prediction['prediction'],
                    'confidence': existing_prediction.get('confidence', 0.85),
                    'model_version': existing_prediction.get('model_version', '1.0')
                },
                'cached': True
            })
        
        # Process prediction
        start_time = time.time()
        cleaned = clean_text(news_text)
        transformed = vectorizer.transform([cleaned])
        prediction = model.predict(transformed)[0]
        
        # Get confidence score and probabilities
        try:
            confidence_scores = model.predict_proba(transformed)[0]
            confidence = float(max(confidence_scores))
            probabilities = {
                'REAL': float(confidence_scores[1]) if len(confidence_scores) > 1 else confidence,
                'FAKE': float(confidence_scores[0]) if len(confidence_scores) > 1 else 1 - confidence
            }
        except Exception as e:
            logger.warning(f"Failed to get confidence scores: {e}")
            confidence = 0.85
            probabilities = {'REAL': 0.85, 'FAKE': 0.15} if prediction == 'REAL' else {'REAL': 0.15, 'FAKE': 0.85}
        
        processing_time = time.time() - start_time
        
        # Extract additional metadata
        language = detect_language(news_text)
        entities = extract_entities(news_text)
        tags = enhanced_extract_tags_from_text(news_text)
        
        # Create enhanced prediction record
        prediction_record = {
            'username': session.get('username', 'anonymous'),
            'news': news_text,
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': probabilities,
            'timestamp': datetime.datetime.now(),
            'source': data.get('source', 'API'),
            'category': data.get('category', 'General'),
            'tags': tags,
            'language': language,
            'entities': entities,
            'content_hash': content_hash,
            'processing_time': processing_time,
            'model_version': '1.0',
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        }
        
        # Save to database
        try:
            result = mongo.db.predictions.insert_one(prediction_record)
            prediction_record['_id'] = result.inserted_id
            logger.info(f"Saved prediction with ID: {result.inserted_id}")
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            # Continue without saving to database
        
        # Convert to card format
        card_data = generate_card_data(prediction_record)
        
        # Clear cache to ensure fresh data
        set_cached_data('stats', None)
        set_cached_data('recent_cards', None)
        
        return jsonify({
            'success': True,
            'card': card_data,
            'prediction': {
                'result': prediction,
                'confidence': confidence,
                'probabilities': probabilities,
                'processing_time': processing_time,
                'model_version': '1.0'
            },
            'metadata': {
                'language': language,
                'entities': entities,
                'tags': tags,
                'word_count': len(news_text.split()),
                'character_count': len(news_text)
            }
        })
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return error_response(f"Prediction failed: {str(e)}", 500)

# Search cards endpoint
@app.route("/api/cards/search", methods=["GET"])
def search_cards():
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return error_response("Search query is required", 400)
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build search query
        search_query = {
            '$or': [
                {'news': {'$regex': query, '$options': 'i'}},
                {'username': {'$regex': query, '$options': 'i'}}
            ]
        }
        
        # Get results
        skip = (page - 1) * limit
        total_count = mongo.db.predictions.count_documents(search_query)
        
        predictions = list(
            mongo.db.predictions
            .find(search_query)
            .sort([('timestamp', -1)])
            .skip(skip)
            .limit(limit)
        )
        
        # Convert to card format
        cards = [generate_card_data(pred) for pred in predictions]
        
        return jsonify({
            'query': query,
            'cards': cards,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'has_more': page * limit < total_count
        })
        
    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        return error_response(f"Search failed: {str(e)}", 500)

# Get card statistics
@app.route("/api/cards/stats", methods=["GET"])
def get_card_stats():
    try:
        # Check cache first
        cached_stats = get_cached_data('stats')
        if cached_stats:
            return jsonify(cached_stats)
        
        # Enhanced statistics aggregation
        pipeline = [
            {
                '$group': {
                    '_id': '$prediction',
                    'count': {'$sum': 1},
                    'avg_confidence': {'$avg': '$confidence'},
                    'min_confidence': {'$min': '$confidence'},
                    'max_confidence': {'$max': '$confidence'}
                }
            }
        ]
        
        stats = list(mongo.db.predictions.aggregate(pipeline))
        
        # Get time-based statistics
        now = datetime.datetime.now()
        time_ranges = {
            'last_hour': now - datetime.timedelta(hours=1),
            'last_24h': now - datetime.timedelta(days=1),
            'last_week': now - datetime.timedelta(weeks=1),
            'last_month': now - datetime.timedelta(days=30)
        }
        
        time_stats = {}
        for period, start_time in time_ranges.items():
            count = mongo.db.predictions.count_documents({
                'timestamp': {'$gte': start_time}
            })
            time_stats[period] = count
        
        # Get top tags
        tag_pipeline = [
            {'$unwind': '$tags'},
            {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        top_tags = list(mongo.db.predictions.aggregate(tag_pipeline))
        
        # Get language distribution
        lang_pipeline = [
            {'$group': {'_id': '$language', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        
        language_stats = list(mongo.db.predictions.aggregate(lang_pipeline))
        
        # Get source distribution
        source_pipeline = [
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        
        source_stats = list(mongo.db.predictions.aggregate(source_pipeline))
        
        # Format response
        result = {
            'total_predictions': mongo.db.predictions.count_documents({}),
            'by_prediction': {},
            'time_based': time_stats,
            'top_tags': [{'tag': item['_id'], 'count': item['count']} for item in top_tags],
            'languages': [{'language': item['_id'], 'count': item['count']} for item in language_stats],
            'sources': [{'source': item['_id'], 'count': item['count']} for item in source_stats],
            'performance': {
                'cache_hit_rate': 0.85,  # Placeholder - can be calculated from actual cache hits
                'avg_processing_time': 0.15  # Placeholder - can be calculated from processing_time field
            }
        }
        
        for stat in stats:
            result['by_prediction'][stat['_id']] = {
                'count': stat['count'],
                'avg_confidence': round(stat.get('avg_confidence', 0), 3),
                'min_confidence': round(stat.get('min_confidence', 0), 3),
                'max_confidence': round(stat.get('max_confidence', 0), 3)
            }
        
        # Cache the results
        set_cached_data('stats', result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return error_response(f"Stats retrieval failed: {str(e)}", 500)

# Batch prediction endpoint
@app.route("/api/predict/batch", methods=["POST"])
@rate_limit(max_requests=5, window=60)  # 5 batch requests per minute
@validate_json_input(required_fields=['articles'])
def predict_batch():
    try:
        data = g.json_data
        articles = data['articles']
        
        if not isinstance(articles, list):
            return error_response("Articles must be a list", 400)
        
        if len(articles) > 10:
            return error_response("Maximum 10 articles per batch", 400)
        
        results = []
        
        for i, article_data in enumerate(articles):
            if not isinstance(article_data, dict) or 'text' not in article_data:
                results.append({
                    'index': i,
                    'error': 'Missing text field',
                    'success': False
                })
                continue
            
            try:
                news_text = article_data['text'].strip()
                
                if len(news_text) < 10 or len(news_text) > 10000:
                    results.append({
                        'index': i,
                        'error': 'Text length must be between 10 and 10,000 characters',
                        'success': False
                    })
                    continue
                
                # Process prediction
                cleaned = clean_text(news_text)
                transformed = vectorizer.transform([cleaned])
                prediction = model.predict(transformed)[0]
                
                try:
                    confidence_scores = model.predict_proba(transformed)[0]
                    confidence = float(max(confidence_scores))
                except:
                    confidence = 0.85
                
                results.append({
                    'index': i,
                    'prediction': prediction,
                    'confidence': confidence,
                    'title': extract_title_from_text(news_text),
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'error': str(e),
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(articles),
            'successful': len([r for r in results if r.get('success', False)]),
            'failed': len([r for r in results if not r.get('success', False)])
        })
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        return error_response(f"Batch prediction failed: {str(e)}", 500)

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        # Check database connection
        mongo.db.command('ping')
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    # Check model availability
    model_status = "healthy" if 'model' in globals() and model is not None else "unhealthy"
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' and model_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'components': {
            'database': db_status,
            'model': model_status,
            'cache': 'healthy'
        },
        'version': '1.0.0'
    })

# Model information endpoint
@app.route("/api/model/info", methods=["GET"])
def model_info():
    try:
        return jsonify({
            'model_version': '1.0',
            'model_type': 'Text Classification',
            'framework': 'scikit-learn',
            'features': {
                'vectorizer': 'TF-IDF',
                'max_features': getattr(vectorizer, 'max_features', 'unknown'),
                'ngram_range': getattr(vectorizer, 'ngram_range', 'unknown')
            },
            'classes': ['FAKE', 'REAL'],
            'last_trained': 'Unknown',  # Can be stored in model metadata
            'performance_metrics': {
                'accuracy': 'Unknown',  # Can be stored from training
                'precision': 'Unknown',
                'recall': 'Unknown',
                'f1_score': 'Unknown'
            }
        })
    except Exception as e:
        return error_response(f"Failed to get model info: {str(e)}", 500)

# API Documentation endpoints
from api_docs import get_api_docs, get_api_docs_html

@app.route("/api/docs", methods=["GET"])
def api_documentation():
    """Return API documentation in OpenAPI format"""
    return get_api_docs()

@app.route("/docs", methods=["GET"])
def api_documentation_html():
    """Return HTML API documentation"""
    return get_api_docs_html()

# Admin endpoints (protected)
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Get detailed admin statistics"""
    # Simple admin check - in production, use proper authentication
    if session.get('username') != 'admin':
        return error_response("Admin access required", 403)
    
    try:
        # Get detailed system statistics
        stats = {
            'database': {
                'total_predictions': mongo.db.predictions.count_documents({}),
                'total_users': mongo.db.users.count_documents({}),
                'database_size': 'Unknown'  # Can be calculated
            },
            'performance': {
                'cache_hit_rate': 0.85,  # Placeholder
                'avg_response_time': 0.15,  # Placeholder
                'error_rate': 0.02  # Placeholder
            },
            'system': {
                'uptime': 'Unknown',  # Can be calculated
                'memory_usage': 'Unknown',  # Can be calculated
                'cpu_usage': 'Unknown'  # Can be calculated
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return error_response(f"Failed to get admin stats: {str(e)}", 500)

@app.route("/api/admin/clear-cache", methods=["POST"])
def admin_clear_cache():
    """Clear application cache"""
    if session.get('username') != 'admin':
        return error_response("Admin access required", 403)
    
    try:
        # Clear cache
        for key in cache:
            cache[key]['data'] = None
            cache[key]['timestamp'] = 0
        
        logger.info("Cache cleared by admin")
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
        
    except Exception as e:
        return error_response(f"Failed to clear cache: {str(e)}", 500)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return error_response("Endpoint not found", 404)
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(error):
    if request.path.startswith('/api/'):
        return error_response("Method not allowed", 405)
    return render_template('405.html'), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return error_response("Internal server error", 500)
    return render_template('500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return error_response("Request entity too large. Maximum file size is 16MB.", 413)

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"{request.method} {request.path} - IP: {request.remote_addr} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
    return response

# CORS headers for all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-Frame-Options', 'DENY')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    return response

# Cleanup function for graceful shutdown
import atexit

def cleanup():
    logger.info("Shutting down application...")
    # Clear cache
    cache.clear()
    # Close database connections if needed
    logger.info("Cleanup completed")

atexit.register(cleanup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting Flask application on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )
