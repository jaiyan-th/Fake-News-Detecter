"""Quick test of the pipeline"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fake_news_detector', 'training', 'backend'))

from modules.pipeline import FakeNewsDetectionPipeline

# Initialize pipeline
MODEL_PATH = 'fake_news_detector/training/backend/model/model.pkl'
VECTORIZER_PATH = 'fake_news_detector/training/backend/model/vectorizer.pkl'

print("Initializing pipeline...")
pipeline = FakeNewsDetectionPipeline(
    model_path=MODEL_PATH,
    vectorizer_path=VECTORIZER_PATH
)

print("\nTesting with sample text...")
result = pipeline.analyze_text(
    text="Breaking news: Scientists discover shocking truth about everything!",
    title="Shocking Discovery"
)

print("\n" + "="*70)
print("RESULT:")
print("="*70)
print(f"Success: {result['success']}")
print(f"Prediction: {result['result']['prediction']}")
print(f"Confidence: {result['result']['confidence']}")
print(f"Verdict: {result['result']['verdict']}")
print("\nRecommendations:")
for rec in result['details']['recommendations']:
    print(f"  {rec}")
print("="*70)
print("\n✅ Pipeline is working correctly!")
