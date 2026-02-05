"""
Fallback Handler for Non-JavaScript Users
Provides basic functionality when JavaScript is disabled
"""

from flask import render_template_string

# Basic HTML template for non-JS users
FALLBACK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fake News Detector - Basic Version</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #f4f6f9;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
        }
        textarea {
            width: 100%;
            min-height: 120px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            resize: vertical;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
        }
        button:hover {
            background: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-weight: 500;
        }
        .result.real {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.fake {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .history {
            margin-top: 40px;
        }
        .history-item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        .history-item.real {
            border-left-color: #28a745;
        }
        .history-item.fake {
            border-left-color: #dc3545;
        }
        .timestamp {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .upgrade-notice {
            background: #e7f3ff;
            border: 1px solid #b8daff;
            color: #004085;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .upgrade-notice strong {
            display: block;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="upgrade-notice">
            <strong>📱 Enhanced Experience Available</strong>
            Enable JavaScript in your browser to access the full card grid interface with advanced features like search, filtering, and interactive cards.
        </div>
        
        <h1>📰 Fake News Detector</h1>
        
        <form method="POST" action="/predict_fallback">
            <div class="form-group">
                <label for="news">Enter news article text:</label>
                <textarea id="news" name="news" placeholder="Paste or type the news article text here..." required>{{ request.form.get('news', '') }}</textarea>
            </div>
            <button type="submit">Analyze Article</button>
        </form>
        
        {% if prediction %}
        <div class="result {{ prediction.lower() }}">
            <strong>Analysis Result:</strong> {{ prediction }}<br>
            <strong>Confidence:</strong> {{ confidence }}%
        </div>
        {% endif %}
        
        {% if error %}
        <div class="result fake">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if history %}
        <div class="history">
            <h2>Recent Analyses</h2>
            {% for item in history %}
            <div class="history-item {{ item.prediction.lower() }}">
                <strong>{{ item.prediction }}</strong> ({{ "%.1f"|format((item.get('confidence', 0.85) * 100)) }}% confidence)
                <div>{{ item.news[:200] }}{% if item.news|length > 200 %}...{% endif %}</div>
                <div class="timestamp">{{ item.timestamp.strftime('%Y-%m-%d %H:%M') }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div style="margin-top: 40px; text-align: center; color: #666; font-size: 14px;">
            <p>This is the basic version of the Fake News Detector.</p>
            <p>For the full experience with card grid layout, enable JavaScript.</p>
        </div>
    </div>
</body>
</html>
"""

def render_fallback_page(prediction=None, confidence=None, error=None, history=None):
    """Render the fallback page for non-JavaScript users"""
    return render_template_string(
        FALLBACK_TEMPLATE,
        prediction=prediction,
        confidence=confidence,
        error=error,
        history=history
    )

def detect_javascript_support(request):
    """Detect if the client supports JavaScript"""
    # Check for common indicators that JavaScript is disabled
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Check for specific headers that indicate JS capability
    accept_header = request.headers.get('Accept', '')
    
    # If the request accepts JSON, likely has JS support
    if 'application/json' in accept_header:
        return True
    
    # Check for AJAX indicators
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    
    # Check for fetch API indicators
    if 'fetch' in request.headers.get('Sec-Fetch-Mode', ''):
        return True
    
    # Check for modern browsers (assume JS support)
    modern_browsers = ['chrome', 'firefox', 'safari', 'edge', 'opera']
    for browser in modern_browsers:
        if browser in user_agent:
            return True
    
    # If it's a regular HTML request from a browser, assume JS support
    if 'text/html' in accept_header and 'mozilla' in user_agent:
        return True
    
    # Default to assuming JS support for modern web
    return True

def should_use_fallback(request):
    """Determine if we should use the fallback interface"""
    # Check if explicitly requesting enhanced interface
    if request.args.get('enhanced') == '1':
        return False
    
    # Check if explicitly requesting fallback
    if request.args.get('fallback') == '1':
        return True
    
    # Check if JavaScript is likely disabled
    if not detect_javascript_support(request):
        return True
    
    # Check for old browsers that might not support modern JS
    user_agent = request.headers.get('User-Agent', '').lower()
    old_browsers = ['msie', 'trident', 'edge/12', 'edge/13', 'edge/14']
    
    for browser in old_browsers:
        if browser in user_agent:
            return True
    
    return False