"""
Enhanced Flask API using the modular pipeline system with authentication
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
import os
import sys
import hashlib
import datetime
import time
from functools import wraps

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.pipeline import FakeNewsDetectionPipeline
from database import get_db

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'fake-news-detector-secret-key-change-in-production')

# Initialize pipeline
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'model.pkl')
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), 'model', 'vectorizer.pkl')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', None)

pipeline = FakeNewsDetectionPipeline(
    model_path=MODEL_PATH,
    vectorizer_path=VECTORIZER_PATH,
    news_api_key=NEWS_API_KEY
)

# Get database instance
db = get_db()


# Authentication decorator
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # Check if this is an AJAX request
            if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': '/login'
                }), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def home():
    """Home page - requires login"""
    username = session.get('username')
    
    # Get user's recent predictions
    predictions = db.get_predictions(username=username, limit=10)
    
    # Get user stats
    total_predictions = db.count_predictions(username=username)
    fake_count = db.count_predictions(username=username, prediction_filter='FAKE')
    real_count = db.count_predictions(username=username, prediction_filter='REAL')
    
    return render_template('index.html', 
                         username=username,
                         predictions=predictions,
                         total_predictions=total_predictions,
                         fake_count=fake_count,
                         real_count=real_count)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        # Get user from database
        user = db.get_user(username)
        
        if user:
            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user['password'] == password_hash:
                session['username'] = username
                session['role'] = user.get('role', 'user')
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User not found', 'error')
        
        return render_template('login.html')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user
        success = db.create_user(username, email, password_hash)
        
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/contact')
def contact():
    """Contact page"""
    username = session.get('username')
    return render_template('contact.html', username=username)


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    username = session.get('username')
    user = db.get_user(username)
    
    # Get user statistics
    total_predictions = db.count_predictions(username=username)
    fake_count = db.count_predictions(username=username, prediction_filter='FAKE')
    real_count = db.count_predictions(username=username, prediction_filter='REAL')
    
    # Get recent activity (last 24 hours)
    from datetime import datetime, timedelta
    recent_time = datetime.now() - timedelta(days=1)
    all_predictions = db.get_predictions(username=username, limit=1000)
    
    # Safe datetime parsing
    recent_activity = 0
    for p in all_predictions:
        try:
            if isinstance(p['timestamp'], str):
                pred_time = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
            else:
                pred_time = p['timestamp']
            
            if pred_time > recent_time:
                recent_activity += 1
        except (ValueError, TypeError):
            continue
    
    # Format stats for template
    stats = {
        'total_predictions': total_predictions,
        'by_prediction': {
            'REAL': real_count,
            'FAKE': fake_count
        },
        'recent_activity': recent_activity
    }
    
    return render_template('profile.html',
                         user=user,
                         stats=stats,
                         total_predictions=total_predictions,
                         fake_count=fake_count,
                         real_count=real_count)


@app.route('/history')
@login_required
def history():
    """User history page"""
    username = session.get('username')
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Get filter parameters
    search = request.args.get('search', '')
    prediction_filter = request.args.get('filter', '')
    sort_by = request.args.get('sort', 'timestamp')
    
    # Get predictions
    predictions = db.get_predictions(
        username=username,
        limit=per_page,
        offset=offset,
        search=search if search else None,
        prediction_filter=prediction_filter if prediction_filter else None,
        sort_by=sort_by
    )
    
    # Get total count for pagination
    total = db.count_predictions(
        username=username,
        search=search if search else None,
        prediction_filter=prediction_filter if prediction_filter else None
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('history.html',
                         predictions=predictions,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         search=search,
                         filter=prediction_filter,
                         sort=sort_by)


@app.route('/past-predictions')
@login_required
def past_predictions():
    """Past predictions dashboard page"""
    username = session.get('username')
    
    # Get user statistics
    total_predictions = db.count_predictions(username=username)
    fake_count = db.count_predictions(username=username, prediction_filter='FAKE')
    real_count = db.count_predictions(username=username, prediction_filter='REAL')
    
    return render_template('past_predictions.html',
                         total_predictions=total_predictions,
                         fake_count=fake_count,
                         real_count=real_count)


@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    """Update user password"""
    username = session.get('username')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validation
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('profile'))
    
    # Verify current password
    user = db.get_user(username)
    current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
    
    if user['password'] != current_password_hash:
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))
    
    # Update password
    new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    success = db.update_user_password(username, new_password_hash)
    
    if success:
        flash('Password updated successfully!', 'success')
    else:
        flash('Failed to update password', 'error')
    
    return redirect(url_for('profile'))


@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    """
    Main analysis endpoint - requires login
    
    Accepts:
    - text: Direct text input
    - url: Article URL
    - title: Optional title
    """
    try:
        data = request.get_json()
        username = session.get('username')
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        start_time = time.time()
        
        # Check input type
        if 'url' in data and data['url']:
            # Analyze from URL
            result = pipeline.analyze_url(data['url'])
            source_url = data['url']
        elif 'text' in data and data['text']:
            # Analyze from text
            title = data.get('title', '')
            result = pipeline.analyze_text(data['text'], title)
            source_url = ''
        else:
            return jsonify({
                'success': False,
                'error': 'Please provide either "text" or "url"'
            }), 400
        
        processing_time = time.time() - start_time
        
        # Save to database if analysis was successful
        if result.get('success'):
            article_text = data.get('text', '')
            article_title = data.get('title', result.get('details', {}).get('article', {}).get('title', ''))
            
            prediction_data = {
                'username': username,
                'news': article_text[:1000],  # Limit text length
                'prediction': result['result']['prediction'],
                'confidence': float(result['result']['confidence'].rstrip('%')) / 100,
                'timestamp': datetime.datetime.now(),
                'source': 'Web Interface',
                'category': 'General',
                'word_count': len(article_text.split()),
                'character_count': len(article_text),
                'content_hash': hashlib.md5(article_text.encode()).hexdigest(),
                'processing_time': processing_time,
                'source_url': source_url,
                'article_title': article_title,
                'credibility_score': result.get('details', {}).get('verification', {}).get('source_credibility', 0.5),
                'sentiment': 'neutral',
                'emotional_score': 0.0
            }
            
            db.create_prediction(prediction_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/test-urls', methods=['GET'])
def get_test_urls():
    """Get a list of test URLs that should work"""
    test_urls = [
        {
            'url': 'test',
            'description': 'Offline Test Mode - No Internet Required',
            'type': 'test_mode'
        },
        {
            'url': 'sample',
            'description': 'Sample Article Analysis',
            'type': 'test_mode'
        }
    ]
    
    return jsonify({
        'success': True,
        'test_urls': test_urls,
        'note': 'Use "test" or "sample" as URL for offline testing'
    })


@app.route('/api/test-analysis', methods=['POST'])
@login_required
def test_analysis():
    """Test the analysis pipeline with sample data"""
    try:
        username = session.get('username')
        
        # Sample news text for testing
        sample_text = """
        Scientists at Stanford University have developed a new artificial intelligence system 
        that can detect misinformation with 94% accuracy. The research, published in the 
        Journal of Computer Science, shows promising results in identifying fake news articles 
        across multiple platforms. The AI system analyzes writing patterns, source credibility, 
        and cross-references facts with verified databases. Lead researcher Dr. Sarah Johnson 
        stated that this breakthrough could help combat the spread of false information online.
        """
        
        sample_title = "Stanford Develops AI System to Combat Fake News"
        
        start_time = time.time()
        result = pipeline.analyze_text(sample_text, sample_title)
        processing_time = time.time() - start_time
        
        # Save to database if successful
        if result.get('success'):
            prediction_data = {
                'username': username,
                'news': sample_text[:1000],
                'prediction': result['result']['prediction'],
                'confidence': float(result['result']['confidence'].rstrip('%')) / 100,
                'timestamp': datetime.datetime.now(),
                'source': 'Test Analysis',
                'word_count': len(sample_text.split()),
                'character_count': len(sample_text),
                'content_hash': hashlib.md5(sample_text.encode()).hexdigest(),
                'processing_time': processing_time,
                'article_title': sample_title
            }
            
            db.create_prediction(prediction_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Test analysis failed'
        }), 500


@app.route('/api/analyze/url', methods=['POST'])
@login_required
def analyze_url():
    """Analyze article from URL - requires login"""
    try:
        data = request.get_json()
        url = data.get('url')
        username = session.get('username')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        # Clean and validate URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        start_time = time.time()
        result = pipeline.analyze_url(url)
        processing_time = time.time() - start_time
        
        # Save to database if successful
        if result.get('success'):
            article_details = result.get('details', {}).get('article', {})
            article_text = article_details.get('content', '')
            article_title = article_details.get('title', 'Untitled Article')
            
            prediction_data = {
                'username': username,
                'news': article_text[:1000] if article_text else article_title,
                'prediction': result['result']['prediction'],
                'confidence': float(result['result']['confidence'].rstrip('%')) / 100,
                'timestamp': datetime.datetime.now(),
                'source': 'URL Analysis',
                'processing_time': processing_time,
                'source_url': url,
                'article_title': article_title,
                'word_count': len(article_text.split()) if article_text else 0,
                'character_count': len(article_text) if article_text else 0
            }
            
            db.create_prediction(prediction_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while processing the URL'
        }), 500


@app.route('/api/analyze/text', methods=['POST'])
@login_required
def analyze_text():
    """Analyze text input - requires login"""
    try:
        data = request.get_json()
        text = data.get('text')
        title = data.get('title', '')
        username = session.get('username')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        start_time = time.time()
        result = pipeline.analyze_text(text, title)
        processing_time = time.time() - start_time
        
        # Save to database
        if result.get('success'):
            prediction_data = {
                'username': username,
                'news': text[:1000],
                'prediction': result['result']['prediction'],
                'confidence': float(result['result']['confidence'].rstrip('%')) / 100,
                'timestamp': datetime.datetime.now(),
                'source': 'Text Input',
                'word_count': len(text.split()),
                'character_count': len(text),
                'content_hash': hashlib.md5(text.encode()).hexdigest(),
                'processing_time': processing_time,
                'article_title': title
            }
            
            db.create_prediction(prediction_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pipeline/info', methods=['GET'])
def pipeline_info():
    """Get pipeline information"""
    try:
        info = pipeline.get_pipeline_info()
        return jsonify({
            'success': True,
            'info': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'pipeline': 'operational',
        'model_loaded': pipeline.classifier.model is not None,
        'vectorizer_loaded': pipeline.feature_extractor.vectorizer is not None,
        'database': 'connected'
    })


@app.route('/api/cards', methods=['GET'])
@login_required
def get_cards():
    """Get user's prediction history as cards"""
    try:
        username = session.get('username')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit
        
        # Get predictions from database
        predictions = db.get_predictions(
            username=username,
            limit=limit,
            offset=offset,
            sort_by='timestamp',
            sort_order='desc'
        )
        
        # Convert predictions to card format
        cards = []
        for pred in predictions:
            cards.append({
                '_id': str(pred['id']),
                'username': pred['username'],
                'text': pred['news'],
                'title': pred.get('article_title', 'Untitled Article'),
                'prediction': pred['prediction'],
                'confidence': pred['confidence'],
                'timestamp': pred['timestamp'],
                'source': pred.get('source', 'Unknown'),
                'likes': 0  # Can be extended later
            })
        
        return jsonify({
            'success': True,
            'cards': cards,
            'page': page,
            'total': db.count_predictions(username=username)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'cards': []
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Fake News Detection System - Enhanced API with Auth")
    print("=" * 60)
    print("\n📊 System Architecture:")
    print("  1️⃣  Data Collection Layer")
    print("  2️⃣  Data Preprocessing")
    print("  3️⃣  Feature Extraction")
    print("  4️⃣  Machine Learning Model")
    print("  5️⃣  Verification Layer")
    print("  6️⃣  Result Dashboard")
    print("\n🔐 Authentication: Enabled")
    print("   • Login required for analysis")
    print("   • User registration available")
    print("   • History tracking enabled")
    print("\n" + "=" * 60)
    
    # Display pipeline info
    info = pipeline.get_pipeline_info()
    print("\n✓ Pipeline Status:")
    for module, status in info['modules'].items():
        print(f"  • {module}: {status}")
    
    print("\n" + "=" * 60)
    print("🌐 Server starting at http://localhost:5000")
    print("   • Login: http://localhost:5000/login")
    print("   • Register: http://localhost:5000/register")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
