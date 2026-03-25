"""Diagnostic test to verify all components"""
import sys
import os

print("="*70)
print("FAKE NEWS DETECTION SYSTEM - DIAGNOSTIC TEST")
print("="*70)

# Test 1: Check Python version
print("\n1. Python Version:")
print(f"   {sys.version}")

# Test 2: Check required packages
print("\n2. Checking Required Packages:")
packages = ['flask', 'flask_cors', 'sklearn', 'pandas', 'numpy', 'nltk', 'bs4', 'requests']
for pkg in packages:
    try:
        __import__(pkg)
        print(f"   ✓ {pkg}")
    except ImportError:
        print(f"   ✗ {pkg} - NOT FOUND")

# Test 3: Check NLTK data
print("\n3. Checking NLTK Data:")
try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt_tab')
        print("   ✓ punkt_tab")
    except:
        print("   ✗ punkt_tab - NOT FOUND")
    
    try:
        nltk.data.find('corpora/stopwords')
        print("   ✓ stopwords")
    except:
        print("   ✗ stopwords - NOT FOUND")
    
    try:
        nltk.data.find('corpora/wordnet')
        print("   ✓ wordnet")
    except:
        print("   ✗ wordnet - NOT FOUND")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Check model files
print("\n4. Checking Model Files:")
model_path = 'fake_news_detector/training/backend/model/model.pkl'
vectorizer_path = 'fake_news_detector/training/backend/model/vectorizer.pkl'

if os.path.exists(model_path):
    print(f"   ✓ model.pkl ({os.path.getsize(model_path)} bytes)")
else:
    print(f"   ✗ model.pkl - NOT FOUND")

if os.path.exists(vectorizer_path):
    print(f"   ✓ vectorizer.pkl ({os.path.getsize(vectorizer_path)} bytes)")
else:
    print(f"   ✗ vectorizer.pkl - NOT FOUND")

# Test 5: Check modules
print("\n5. Checking Custom Modules:")
sys.path.insert(0, 'fake_news_detector/training/backend')
modules_to_check = [
    'modules.data_collection',
    'modules.data_preprocessing',
    'modules.feature_extraction',
    'modules.ml_model',
    'modules.verification',
    'modules.dashboard',
    'modules.pipeline'
]

for mod in modules_to_check:
    try:
        __import__(mod)
        print(f"   ✓ {mod}")
    except Exception as e:
        print(f"   ✗ {mod} - Error: {str(e)[:50]}")

# Test 6: Quick pipeline test
print("\n6. Testing Pipeline:")
try:
    from modules.pipeline import FakeNewsDetectionPipeline
    
    pipeline = FakeNewsDetectionPipeline(
        model_path='model/model.pkl',
        vectorizer_path='model/vectorizer.pkl'
    )
    print("   ✓ Pipeline initialized")
    
    # Quick test
    result = pipeline.analyze_text("This is a test", "Test")
    if result['success']:
        print(f"   ✓ Analysis successful: {result['result']['prediction']}")
    else:
        print(f"   ✗ Analysis failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"   ✗ Pipeline error: {str(e)[:100]}")

print("\n" + "="*70)
print("DIAGNOSTIC TEST COMPLETE")
print("="*70)
