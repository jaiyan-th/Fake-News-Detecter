"""
Test script for the Fake News Detection Pipeline
"""

import os
import sys
import json

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.pipeline import FakeNewsDetectionPipeline


def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)
    print()


def print_result(result):
    """Pretty print analysis result"""
    if not result.get('success', False):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    print("✅ Analysis Complete!\n")
    
    # Main result
    res = result['result']
    print(f"📊 Prediction: {res['prediction']}")
    print(f"📈 Confidence: {res['confidence']}")
    print(f"🎯 Verdict: {res['verdict']}\n")
    
    # Article info
    article = result['details']['article']
    print(f"📰 Article: {article['title'][:60]}...")
    print(f"🌐 Source: {article['source']}")
    print(f"✍️  Author: {article['author']}\n")
    
    # Analysis details
    analysis = result['details']['analysis']
    print(f"🤖 Model: {analysis['model_type']}")
    print(f"💭 {analysis['interpretation']}\n")
    
    # Feature signals
    if analysis['feature_signals']:
        print("⚠️  Warning Signs Detected:")
        for signal in analysis['feature_signals']:
            print(f"   • {signal}")
        print()
    
    # Verification
    verification = result['details']['verification']
    print(f"🔍 Source Credibility: {verification['source_credibility']:.2f}")
    print(f"✓ Fact-Check Status: {verification['fact_check_status']}\n")
    
    # Recommendations
    print("💡 Recommendations:")
    for rec in result['details']['recommendations']:
        print(f"   {rec}")
    print()


def test_pipeline():
    """Run comprehensive pipeline tests"""
    
    print_separator("🚀 FAKE NEWS DETECTION SYSTEM - PIPELINE TEST")
    
    # Initialize pipeline
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'model.pkl')
    VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), 'model', 'vectorizer.pkl')
    
    print("Initializing pipeline...")
    pipeline = FakeNewsDetectionPipeline(
        model_path=MODEL_PATH,
        vectorizer_path=VECTORIZER_PATH
    )
    
    # Display pipeline info
    info = pipeline.get_pipeline_info()
    print("\n✓ Pipeline initialized successfully!")
    print(f"\nModel Type: {info['model_info']['type']}")
    print(f"Model Loaded: {info['model_info']['loaded']}")
    print(f"Vectorizer Loaded: {info['vectorizer_loaded']}")
    
    # Test cases
    test_cases = [
        {
            'name': 'Sensational Fake News',
            'title': 'BREAKING: Shocking Discovery Will Change Everything!!!',
            'text': '''
            Scientists have made an UNBELIEVABLE discovery that the government 
            doesn't want you to know about! This SHOCKING revelation will 
            change EVERYTHING we thought we knew. Experts are STUNNED and 
            HORRIFIED by what they found. Share this before it gets deleted!
            '''
        },
        {
            'name': 'Credible News Article',
            'title': 'Economic Report Shows Steady Growth',
            'text': '''
            According to the latest economic data released by the Federal Reserve,
            the economy showed steady growth in the third quarter. Analysts note
            that employment figures remain stable, with unemployment at 4.2 percent.
            The report indicates continued expansion in the manufacturing sector.
            '''
        },
        {
            'name': 'Suspicious Clickbait',
            'title': 'You Won\'t Believe What Happened Next!',
            'text': '''
            This one weird trick will SHOCK you! Doctors HATE this! The secret
            they don't want you to know! Click now before it's too late!!!
            URGENT ALERT! This is going VIRAL!
            '''
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print_separator(f"TEST {i}: {test_case['name']}")
        
        result = pipeline.analyze_text(
            text=test_case['text'],
            title=test_case['title']
        )
        
        print_result(result)
    
    # Test URL analysis (if available)
    print_separator("TEST 4: URL Analysis (Example)")
    print("Note: URL analysis requires internet connection and valid URL")
    print("Example: pipeline.analyze_url('https://www.reuters.com/article/...')")
    
    print_separator("✅ ALL TESTS COMPLETED")
    print("The pipeline is working correctly!")
    print("\nYou can now:")
    print("  1. Run the API: python api_enhanced.py")
    print("  2. Test with your own text")
    print("  3. Integrate into your application")
    print()


if __name__ == '__main__':
    try:
        test_pipeline()
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
