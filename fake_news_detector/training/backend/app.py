from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
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
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

# Import our SQLite database manager
from database import get_db

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
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "model", "model.pkl")
vectorizer_path = os.path.join(base_dir, "model", "vectorizer.pkl")

with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Enable CORS for frontend integration
CORS(app, origins=["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:8080"])

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Get database instance
db = get_db()

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
        'id': str(prediction_record['id']),
        'title': extract_title_from_text(news_text),
        'content': news_text,
        'prediction': prediction_record['prediction'],
        'confidence': prediction_record.get('confidence', 0.85),
        'timestamp': prediction_record['timestamp'],
        'username': prediction_record['username'],
        'imageUrl': generate_placeholder_image_url(prediction_record['prediction']),
        'source': prediction_record.get('source', 'User Submission'),
        'category': prediction_record.get('category', 'General'),
        'tags': prediction_record.get('tags', []),
        'language': prediction_record.get('language', 'en'),
        'word_count': prediction_record.get('word_count', len(news_text.split())),
        'character_count': prediction_record.get('character_count', len(news_text)),
        'content_hash': prediction_record.get('content_hash', generate_content_hash(news_text)),
        'entities': prediction_record.get('entities', {}),
        'model_version': prediction_record.get('model_version', '1.0')
    }

def generate_placeholder_image_url(prediction):
    """Generate placeholder image URL based on prediction"""
    color = "10b981" if prediction == "REAL" else "ef4444"
    return f"https://via.placeholder.com/300x200/{color}/ffffff?text={prediction}"

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

def extract_article_from_url(url):
    """Extract article content from URL"""
    try:
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to extract title
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        
        # Try to extract main content using common article selectors
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main',
            '.article-body',
            '.story-body'
        ]
        
        article_text = ""
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                article_text = content_div.get_text(separator=' ', strip=True)
                break
        
        # Fallback: extract all paragraph text
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
        
        # Clean up the text
        article_text = re.sub(r'\s+', ' ', article_text).strip()
        
        # Extract domain for source
        domain = urlparse(url).netloc
        
        return {
            'title': title,
            'content': article_text,
            'source': domain,
            'url': url,
            'success': True
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to fetch URL: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to parse article: {str(e)}'
        }

def get_source_credibility_score(domain):
    """Get credibility score for news source"""
    # This is a simplified credibility scoring system
    # In a real application, you'd use a comprehensive database of news sources
    
    high_credibility = [
        'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'pbs.org',
        'wsj.com', 'nytimes.com', 'washingtonpost.com', 'theguardian.com',
        'economist.com', 'time.com', 'newsweek.com', 'usatoday.com'
    ]
    
    medium_credibility = [
        'cnn.com', 'foxnews.com', 'msnbc.com', 'cbsnews.com', 'abcnews.go.com',
        'nbcnews.com', 'politico.com', 'thehill.com', 'axios.com'
    ]
    
    low_credibility = [
        'infowars.com', 'breitbart.com', 'naturalnews.com', 'beforeitsnews.com',
        'worldnewsdailyreport.com', 'theonion.com'
    ]
    
    domain_lower = domain.lower()
    
    for trusted in high_credibility:
        if trusted in domain_lower:
            return {'score': 0.9, 'level': 'High', 'color': 'green'}
    
    for medium in medium_credibility:
        if medium in domain_lower:
            return {'score': 0.7, 'level': 'Medium', 'color': 'orange'}
    
    for low in low_credibility:
        if low in domain_lower:
            return {'score': 0.3, 'level': 'Low', 'color': 'red'}
    
    # Unknown source
    return {'score': 0.5, 'level': 'Unknown', 'color': 'gray'}

def analyze_sentiment(text):
    """Simple sentiment analysis"""
    # This is a basic sentiment analysis
    # In production, you'd use a proper NLP library like TextBlob or VADER
    
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'success', 'win', 'best']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'fail', 'disaster', 'crisis', 'danger', 'threat']
    emotional_words = ['shocking', 'unbelievable', 'incredible', 'outrageous', 'devastating', 'explosive', 'breaking']
    
    text_lower = text.lower()
    words = text_lower.split()
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    emotional_count = sum(1 for word in words if word in emotional_words)
    
    total_words = len(words)
    if total_words == 0:
        return {'sentiment': 'neutral', 'emotional_score': 0}
    
    sentiment_score = (positive_count - negative_count) / total_words
    emotional_score = emotional_count / total_words
    
    if sentiment_score > 0.02:
        sentiment = 'positive'
    elif sentiment_score < -0.02:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'emotional_score': emotional_score,
        'emotional_level': 'high' if emotional_score > 0.05 else 'medium' if emotional_score > 0.02 else 'low'
    }

def explain_prediction_confidence(text, prediction, confidence, vectorizer, model):
    """Generate explanation for AI prediction confidence"""
    try:
        # Get feature importance from the model
        cleaned_text = clean_text(text)
        transformed = vectorizer.transform([cleaned_text])
        
        # Get feature names and their weights
        feature_names = vectorizer.get_feature_names_out()
        
        # For linear models, we can get feature importance
        if hasattr(model, 'coef_'):
            feature_weights = model.coef_[0]
            
            # Get the features that were actually used in this text
            feature_indices = transformed.nonzero()[1]
            feature_scores = []
            
            for idx in feature_indices:
                word = feature_names[idx]
                weight = feature_weights[idx]
                tf_idf_score = transformed[0, idx]
                impact = weight * tf_idf_score
                
                feature_scores.append({
                    'word': word,
                    'weight': float(weight),
                    'tf_idf': float(tf_idf_score),
                    'impact': float(impact)
                })
            
            # Sort by absolute impact
            feature_scores.sort(key=lambda x: abs(x['impact']), reverse=True)
            
            # Get top positive and negative indicators
            positive_indicators = [f for f in feature_scores if f['impact'] > 0][:5]
            negative_indicators = [f for f in feature_scores if f['impact'] < 0][:5]
            
            # Generate explanation
            explanation = {
                'confidence_level': 'high' if confidence > 0.8 else 'medium' if confidence > 0.6 else 'low',
                'key_factors': {
                    'real_indicators': positive_indicators if prediction == 'REAL' else negative_indicators,
                    'fake_indicators': negative_indicators if prediction == 'REAL' else positive_indicators
                },
                'analysis_summary': generate_explanation_summary(prediction, confidence, positive_indicators, negative_indicators),
                'technical_details': {
                    'model_type': 'Linear Classification',
                    'features_analyzed': len(feature_indices),
                    'total_vocabulary': len(feature_names)
                }
            }
            
            return explanation
            
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        
    # Fallback explanation
    return {
        'confidence_level': 'medium',
        'analysis_summary': f"The AI model analyzed the text and predicted it as {prediction} with {confidence*100:.1f}% confidence based on learned patterns from training data.",
        'key_factors': {
            'real_indicators': [],
            'fake_indicators': []
        },
        'technical_details': {
            'model_type': 'Machine Learning Classification',
            'note': 'Detailed feature analysis unavailable'
        }
    }

def generate_explanation_summary(prediction, confidence, positive_indicators, negative_indicators):
    """Generate human-readable explanation summary"""
    confidence_pct = confidence * 100
    
    if prediction == 'REAL':
        main_indicators = positive_indicators
        counter_indicators = negative_indicators
        prediction_text = "legitimate news"
    else:
        main_indicators = negative_indicators
        counter_indicators = positive_indicators
        prediction_text = "potentially fake news"
    
    summary = f"The AI model classified this article as {prediction_text} with {confidence_pct:.1f}% confidence. "
    
    if main_indicators:
        top_words = [ind['word'] for ind in main_indicators[:3]]
        summary += f"Key supporting factors include words/phrases like: {', '.join(top_words)}. "
    
    if counter_indicators:
        counter_words = [ind['word'] for ind in counter_indicators[:2]]
        summary += f"Some opposing signals were detected: {', '.join(counter_words)}. "
    
    if confidence > 0.8:
        summary += "The high confidence suggests strong alignment with learned patterns."
    elif confidence > 0.6:
        summary += "The moderate confidence indicates some mixed signals in the text."
    else:
        summary += "The low confidence suggests the text has ambiguous characteristics."
    
    return summary

def find_similar_articles(text, limit=5):
    """Find similar articles in the database"""
    try:
        # Get all articles from database
        all_articles = db.get_predictions(limit=100)  # Get recent 100 articles
        
        if len(all_articles) < 2:
            return []
        
        # Simple similarity based on common words and length
        text_words = set(clean_text(text).lower().split())
        text_length = len(text)
        
        similarities = []
        
        for article in all_articles:
            if article['news'] == text:  # Skip the same article
                continue
                
            article_words = set(clean_text(article['news']).lower().split())
            article_length = len(article['news'])
            
            # Calculate Jaccard similarity for words
            intersection = len(text_words.intersection(article_words))
            union = len(text_words.union(article_words))
            word_similarity = intersection / union if union > 0 else 0
            
            # Length similarity
            length_similarity = 1 - abs(text_length - article_length) / max(text_length, article_length)
            
            # Combined similarity score
            combined_score = (word_similarity * 0.7) + (length_similarity * 0.3)
            
            if combined_score > 0.1:  # Only include if somewhat similar
                similarities.append({
                    'article': article,
                    'similarity_score': combined_score,
                    'word_similarity': word_similarity,
                    'length_similarity': length_similarity
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:limit]
        
    except Exception as e:
        logger.error(f"Failed to find similar articles: {e}")
        return []

def get_trending_topics():
    """Get trending fake news topics from recent analyses"""
    try:
        # Get recent articles (last 7 days)
        recent_date = datetime.datetime.now() - datetime.timedelta(days=7)
        recent_articles = db.get_predictions(limit=50)
        
        # Filter by date and fake news
        fake_articles = [
            article for article in recent_articles 
            if article['prediction'] == 'FAKE' and 
            datetime.datetime.fromisoformat(str(article['timestamp'])) > recent_date
        ]
        
        if not fake_articles:
            return []
        
        # Extract common themes/topics
        topic_keywords = {}
        
        for article in fake_articles:
            tags = article.get('tags', [])
            for tag in tags:
                if tag not in topic_keywords:
                    topic_keywords[tag] = {
                        'count': 0,
                        'articles': [],
                        'avg_confidence': 0
                    }
                topic_keywords[tag]['count'] += 1
                topic_keywords[tag]['articles'].append(article)
        
        # Calculate average confidence for each topic
        for topic in topic_keywords:
            articles = topic_keywords[topic]['articles']
            avg_conf = sum(article.get('confidence', 0) for article in articles) / len(articles)
            topic_keywords[topic]['avg_confidence'] = avg_conf
        
        # Sort by frequency and return trending topics
        trending = [
            {
                'topic': topic,
                'count': data['count'],
                'avg_confidence': data['avg_confidence'],
                'trend_level': 'high' if data['count'] >= 5 else 'medium' if data['count'] >= 3 else 'low'
            }
            for topic, data in topic_keywords.items()
            if data['count'] >= 2  # At least 2 articles
        ]
        
        trending.sort(key=lambda x: x['count'], reverse=True)
        return trending[:10]
        
    except Exception as e:
        logger.error(f"Failed to get trending topics: {e}")
        return []

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
    return render_template("index.html", username=session.get('username'))

# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            return render_template("login.html", error="Please enter both username and password")
        
        user = db.get_user(username)
        
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["user_id"] = str(user["id"])
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password")
    
    success_message = request.args.get("success")
    return render_template("login.html", success=success_message)

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
        
        # Check if user already exists
        if db.get_user(username):
            return render_template("register.html", error="Username already exists")
        
        if db.get_user_by_email(email):
            return render_template("register.html", error="Email already registered")
        
        # Create new user
        hashed_password = generate_password_hash(password)
        if db.create_user(username, email, hashed_password):
            return redirect(url_for("login", success="Account created successfully! Please log in."))
        else:
            return render_template("register.html", error="Failed to create account")
    
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

        # Create prediction record
        prediction_data = {
            "username": session["username"],
            "news": news,
            "prediction": result,
            "confidence": confidence,
            "timestamp": datetime.datetime.now(),
            "source": "Web Interface",
            "model_version": "1.0",
            "word_count": len(news.split()),
            "character_count": len(news),
            "content_hash": generate_content_hash(news)
        }
        
        db.create_prediction(prediction_data)

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
        predictions = db.get_predictions(username=username, limit=50)
        
        return render_template("history.html", predictions=predictions, username=username)
    except Exception as e:
        return render_template("history.html", error=str(e), username=session.get('username'))

# Clear History
@app.route("/clear_history", methods=["POST"])
def clear_history():
    if "username" not in session:
        return redirect(url_for("login"))

    db.delete_user_predictions(session["username"])
    return redirect(url_for("history"))

# Admin View (restricted)
@app.route("/admin")
def admin():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if session["username"] != "admin":
        return "Access denied. Admins only."

    records = db.get_predictions(limit=100)
    return render_template("admin.html", records=records)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Profile route
@app.route("/profile")
@login_required
def profile():
    user = db.get_user(session["username"])
    # Get user stats
    stats = db.get_statistics()
    # Filter stats for current user if possible, or just show global + user specific
    # For now, let's calculate user specific stats simple way
    user_predictions = db.get_predictions(username=session["username"], limit=1000)
    user_stats = {
        "total_predictions": len(user_predictions),
        "by_prediction": {"REAL": 0, "FAKE": 0},
        "recent_activity": 0
    }
    for p in user_predictions:
        if p["prediction"] in user_stats["by_prediction"]:
            user_stats["by_prediction"][p["prediction"]] += 1
    
    # Recent activity (24h)
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    user_stats["recent_activity"] = sum(1 for p in user_predictions if datetime.datetime.fromisoformat(str(p["timestamp"])) > yesterday)
    
    return render_template("profile.html", user=user, stats=user_stats)

@app.route("/update_password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    user = db.get_user(session["username"])
    
    if not check_password_hash(user["password"], current_password):
        flash("Incorrect current password", "error")
        return redirect(url_for("profile"))
        
    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect(url_for("profile"))
        
    if len(new_password) < 6:
        flash("Password must be at least 6 characters", "error")
        return redirect(url_for("profile"))
        
    hashed_password = generate_password_hash(new_password)
    if db.update_user_password(session["username"], hashed_password):
        flash("Password updated successfully!", "success")
    else:
        flash("Failed to update password", "error")
        
    return redirect(url_for("profile"))

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
            
        # Calculate skip value
        offset = (page - 1) * limit
        
        # Get total count for pagination
        total_count = db.count_predictions(search=search, prediction_filter=filter_prediction)
        
        # Get paginated results
        predictions = db.get_predictions(
            limit=limit, 
            offset=offset, 
            search=search, 
            prediction_filter=filter_prediction,
            sort_by=sort_by,
            sort_order=sort_order
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
@app.route("/api/cards/<int:card_id>", methods=["GET"])
def get_card_details(card_id):
    try:
        # Find the prediction record
        prediction = db.get_prediction_by_id(card_id)
        
        if not prediction:
            return error_response("Card not found", 404)
        
        # Convert to detailed card format
        card_data = generate_card_data(prediction)
        
        # Add additional details for modal view
        card_data.update({
            'full_content': prediction['news'],
            'word_count': prediction.get('word_count', len(prediction['news'].split())),
            'character_count': prediction.get('character_count', len(prediction['news'])),
            'analysis': {
                'prediction': prediction['prediction'],
                'confidence': prediction.get('confidence', 0.85),
                'model_version': prediction.get('model_version', '1.0'),
                'processed_at': prediction['timestamp']
            }
        })
        
        return jsonify(card_data)
        
    except Exception as e:
        return error_response(f"Server error: {str(e)}", 500)

# URL analysis endpoint
@app.route("/api/analyze-url", methods=["POST"])
@rate_limit(max_requests=20, window=60)  # 20 URL requests per minute
@validate_json_input(required_fields=['url'])
def analyze_url():
    try:
        data = g.json_data
        url = data['url'].strip()
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            return error_response("Please provide a valid URL starting with http:// or https://", 400)
        
        # Extract article from URL
        extraction_result = extract_article_from_url(url)
        
        if not extraction_result['success']:
            return error_response(extraction_result['error'], 400)
        
        article_text = extraction_result['content']
        article_title = extraction_result['title']
        source_domain = extraction_result['source']
        
        if len(article_text) < 50:
            return error_response("Could not extract enough content from the URL. Please try a different article.", 400)
        
        # Get source credibility
        credibility = get_source_credibility_score(source_domain)
        
        # Analyze sentiment
        sentiment_analysis = analyze_sentiment(article_text)
        
        # Process with ML model
        start_time = time.time()
        cleaned = clean_text(article_text)
        transformed = vectorizer.transform([cleaned])
        prediction = model.predict(transformed)[0]
        
        # Get confidence score
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
        
        # Extract metadata
        language = detect_language(article_text)
        entities = extract_entities(article_text)
        tags = enhanced_extract_tags_from_text(article_text)
        
        # Create enhanced prediction record
        prediction_record = {
            'username': session.get('username', 'anonymous'),
            'news': article_text,
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': probabilities,
            'timestamp': datetime.datetime.now(),
            'source': source_domain,
            'category': 'URL Analysis',
            'tags': tags,
            'language': language,
            'entities': entities,
            'content_hash': generate_content_hash(article_text),
            'processing_time': processing_time,
            'model_version': '1.0',
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'word_count': len(article_text.split()),
            'character_count': len(article_text),
            'source_url': url,
            'article_title': article_title,
            'credibility_score': credibility['score'],
            'sentiment': sentiment_analysis['sentiment'],
            'emotional_score': sentiment_analysis['emotional_score']
        }
        
        # Save to database
        try:
            prediction_id = db.create_prediction(prediction_record)
            prediction_record['id'] = prediction_id
            logger.info(f"Saved URL analysis with ID: {prediction_id}")
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
        
        # Convert to card format
        card_data = generate_card_data(prediction_record)
        card_data['title'] = article_title or card_data['title']
        
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
            'url_analysis': {
                'title': article_title,
                'source_domain': source_domain,
                'credibility': credibility,
                'sentiment': sentiment_analysis,
                'extracted_length': len(article_text)
            },
            'metadata': {
                'language': language,
                'entities': entities,
                'tags': tags,
                'word_count': len(article_text.split()),
                'character_count': len(article_text)
            }
        })
        
    except Exception as e:
        logger.error(f"URL analysis failed: {e}")
        return error_response(f"URL analysis failed: {str(e)}", 500)

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
        existing_prediction = db.get_prediction_by_hash(content_hash)
        
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
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'word_count': len(news_text.split()),
            'character_count': len(news_text)
        }
        
        # Save to database
        try:
            prediction_id = db.create_prediction(prediction_record)
            prediction_record['id'] = prediction_id
            logger.info(f"Saved prediction with ID: {prediction_id}")
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            # Continue without saving to database
        
        # Convert to card format
        card_data = generate_card_data(prediction_record)
        
        # Generate explanation
        explanation = explain_prediction_confidence(news_text, prediction, confidence, vectorizer, model)
        
        # Find similar articles
        similar_articles = find_similar_articles(news_text, limit=3)
        similar_cards = [generate_card_data(sim['article']) for sim in similar_articles]
        
        # Clear cache to ensure fresh data
        set_cached_data('stats', None)
        
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
            'explanation': explanation,
            'similar_articles': similar_cards,
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

# Get card statistics
@app.route("/api/cards/stats", methods=["GET"])
def get_card_stats():
    try:
        # Check cache first
        cached_stats = get_cached_data('stats')
        if cached_stats:
            return jsonify(cached_stats)
        
        # Get statistics from database
        stats = db.get_statistics()
        
        # Format response
        result = {
            'total_predictions': stats['total_predictions'],
            'by_prediction': {
                pred: {'count': count, 'avg_confidence': 0.85, 'min_confidence': 0.5, 'max_confidence': 0.99}
                for pred, count in stats['by_prediction'].items()
            },
            'recent_activity': stats['recent_activity'],
            'top_users': stats['top_users']
        }
        
        # Cache the results
        set_cached_data('stats', result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return error_response(f"Stats retrieval failed: {str(e)}", 500)

# Confidence explanation endpoint
@app.route("/api/explain/<int:prediction_id>", methods=["GET"])
def explain_prediction(prediction_id):
    try:
        # Get the prediction from database
        prediction = db.get_prediction_by_id(prediction_id)
        
        if not prediction:
            return error_response("Prediction not found", 404)
        
        # Generate explanation
        explanation = explain_prediction_confidence(
            prediction['news'], 
            prediction['prediction'], 
            prediction['confidence'],
            vectorizer,
            model
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'prediction_id': prediction_id
        })
        
    except Exception as e:
        logger.error(f"Failed to explain prediction: {e}")
        return error_response(f"Failed to generate explanation: {str(e)}", 500)

# Similar articles endpoint
@app.route("/api/similar/<int:prediction_id>", methods=["GET"])
def get_similar_articles(prediction_id):
    try:
        # Get the prediction from database
        prediction = db.get_prediction_by_id(prediction_id)
        
        if not prediction:
            return error_response("Prediction not found", 404)
        
        # Find similar articles
        similar_articles = find_similar_articles(prediction['news'])
        
        # Convert to card format
        similar_cards = []
        for similarity_data in similar_articles:
            article = similarity_data['article']
            card = generate_card_data(article)
            card['similarity_score'] = similarity_data['similarity_score']
            card['similarity_percentage'] = round(similarity_data['similarity_score'] * 100, 1)
            similar_cards.append(card)
        
        return jsonify({
            'success': True,
            'similar_articles': similar_cards,
            'total_found': len(similar_cards),
            'prediction_id': prediction_id
        })
        
    except Exception as e:
        logger.error(f"Failed to find similar articles: {e}")
        return error_response(f"Failed to find similar articles: {str(e)}", 500)

# Trending topics endpoint
@app.route("/api/trending", methods=["GET"])
def trending_topics_endpoint():
    try:
        trending_topics = get_trending_topics()
        
        return jsonify({
            'success': True,
            'trending_topics': trending_topics,
            'last_updated': datetime.datetime.now().isoformat(),
            'analysis_period': '7 days'
        })
        
    except Exception as e:
        logger.error(f"Failed to get trending topics: {e}")
        return error_response(f"Failed to get trending topics: {str(e)}", 500)

# Real-time monitoring dashboard endpoint
@app.route("/api/monitoring/dashboard", methods=["GET"])
def get_monitoring_dashboard():
    try:
        # Get recent activity (last 24 hours)
        recent_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        recent_articles = db.get_predictions(limit=100)
        
        # Filter recent articles
        recent_filtered = [
            article for article in recent_articles 
            if datetime.datetime.fromisoformat(str(article['timestamp'])) > recent_date
        ]
        
        # Calculate metrics
        total_recent = len(recent_filtered)
        fake_recent = len([a for a in recent_filtered if a['prediction'] == 'FAKE'])
        real_recent = total_recent - fake_recent
        
        # Get trending topics
        trending = get_trending_topics()
        
        # Calculate hourly activity
        hourly_activity = {}
        for article in recent_filtered:
            hour = datetime.datetime.fromisoformat(str(article['timestamp'])).hour
            if hour not in hourly_activity:
                hourly_activity[hour] = {'total': 0, 'fake': 0, 'real': 0}
            hourly_activity[hour]['total'] += 1
            if article['prediction'] == 'FAKE':
                hourly_activity[hour]['fake'] += 1
            else:
                hourly_activity[hour]['real'] += 1
        
        return jsonify({
            'success': True,
            'monitoring_data': {
                'last_24h_stats': {
                    'total_analyzed': total_recent,
                    'fake_detected': fake_recent,
                    'real_verified': real_recent,
                    'fake_percentage': round((fake_recent / total_recent * 100) if total_recent > 0 else 0, 1)
                },
                'trending_topics': trending,
                'hourly_activity': hourly_activity,
                'alert_level': 'high' if fake_recent > total_recent * 0.6 else 'medium' if fake_recent > total_recent * 0.3 else 'low',
                'last_updated': datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        return error_response(f"Failed to get monitoring data: {str(e)}", 500)

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        # Check database connection
        stats = db.get_statistics()
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting Flask application on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Using SQLite database at: {db.db_path}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )