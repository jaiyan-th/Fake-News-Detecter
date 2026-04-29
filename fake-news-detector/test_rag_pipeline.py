"""
Test script for RAG Pipeline
Demonstrates the 11-step verification process
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_pipeline import RAGPipeline
from services.extractor import ArticleContent
import json


def test_rag_pipeline_url():
    """Test RAG pipeline with a URL"""
    print("=" * 80)
    print("RAG PIPELINE TEST - URL Analysis")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = RAGPipeline(
        groq_api_key=os.getenv('GROQ_API_KEY'),
        news_api_key=os.getenv('NEWS_API_KEY'),
        serpapi_key=os.getenv('SERPAPI_KEY')
    )
    
    # Test URL (replace with actual news URL)
    test_url = "https://www.bbc.com/news/world"
    
    print(f"\nAnalyzing URL: {test_url}")
    print("-" * 80)
    
    # Extract content
    from services.extractor import ContentExtractor
    extractor = ContentExtractor()
    
    try:
        article = extractor.extract_content(test_url)
        print(f"\n✓ Content extracted successfully")
        print(f"  Title: {article.title[:100]}...")
        print(f"  Content length: {len(article.content)} characters")
        print(f"  Source: {article.source}")
    except Exception as e:
        print(f"\n✗ Content extraction failed: {e}")
        return
    
    # Run RAG pipeline
    print("\n" + "=" * 80)
    print("Running RAG Pipeline (11 steps)...")
    print("=" * 80 + "\n")
    
    try:
        result = pipeline.analyze(article)
        
        # Display results
        print("\n" + "=" * 80)
        print("RAG PIPELINE RESULTS")
        print("=" * 80)
        
        print(f"\n📊 VERDICT: {result.verdict}")
        print(f"📈 CONFIDENCE: {result.confidence:.1f}%")
        print(f"📝 CLAIM: {result.claim_summary}")
        print(f"⏱️  PROCESSING TIME: {result.processing_time:.2f}s")
        
        print(f"\n🌐 NEWS API EVIDENCE ({len(result.news_api_evidence)} sources):")
        for i, ev in enumerate(result.news_api_evidence, 1):
            print(f"  {i}. [{ev.stance.value.upper()}] {ev.source}")
            print(f"     Title: {ev.title[:80]}...")
            print(f"     Similarity: {ev.similarity_score:.2f}")
        
        print(f"\n📚 RAG EVIDENCE ({len(result.rag_evidence)} historical matches):")
        for i, ev in enumerate(result.rag_evidence, 1):
            print(f"  {i}. [{ev.stance.value.upper()}] {ev.source}")
            print(f"     Content: {ev.content[:80]}...")
            print(f"     Similarity: {ev.similarity:.2f}")
        
        print(f"\n🔍 GAP ANALYSIS: {result.gap_analysis}")
        print(f"\n💭 REASONING:\n{result.reasoning}")
        print(f"\n📋 EXPLANATION:\n{result.final_explanation}")
        
        # Display JSON output
        print("\n" + "=" * 80)
        print("JSON OUTPUT (STEP 11)")
        print("=" * 80)
        json_output = pipeline.to_json(result)
        print(json.dumps(json_output, indent=2))
        
    except Exception as e:
        print(f"\n✗ RAG pipeline failed: {e}")
        import traceback
        traceback.print_exc()


def test_rag_pipeline_text():
    """Test RAG pipeline with text content"""
    print("\n\n" + "=" * 80)
    print("RAG PIPELINE TEST - Text Analysis")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = RAGPipeline(
        groq_api_key=os.getenv('GROQ_API_KEY'),
        news_api_key=os.getenv('NEWS_API_KEY'),
        serpapi_key=os.getenv('SERPAPI_KEY')
    )
    
    # Test text (example claim)
    test_text = """
    Breaking: Scientists discover new planet in our solar system. 
    Astronomers at NASA have confirmed the existence of a ninth planet 
    beyond Neptune's orbit. The planet, tentatively named "Planet X", 
    is estimated to be 10 times the mass of Earth and orbits the Sun 
    once every 10,000 years. The discovery was made using advanced 
    telescopes and computer modeling.
    """
    
    print(f"\nAnalyzing text content:")
    print("-" * 80)
    print(test_text.strip())
    print("-" * 80)
    
    # Create ArticleContent
    article = ArticleContent(
        title="Scientists discover new planet in our solar system",
        content=test_text.strip(),
        url="",
        source=""
    )
    
    # Run RAG pipeline
    print("\n" + "=" * 80)
    print("Running RAG Pipeline (11 steps)...")
    print("=" * 80 + "\n")
    
    try:
        result = pipeline.analyze(article)
        
        # Display results
        print("\n" + "=" * 80)
        print("RAG PIPELINE RESULTS")
        print("=" * 80)
        
        print(f"\n📊 VERDICT: {result.verdict}")
        print(f"📈 CONFIDENCE: {result.confidence:.1f}%")
        print(f"📝 CLAIM: {result.claim_summary}")
        print(f"⏱️  PROCESSING TIME: {result.processing_time:.2f}s")
        
        print(f"\n🌐 NEWS API EVIDENCE ({len(result.news_api_evidence)} sources):")
        for i, ev in enumerate(result.news_api_evidence, 1):
            print(f"  {i}. [{ev.stance.value.upper()}] {ev.source}")
            print(f"     Title: {ev.title[:80]}...")
        
        print(f"\n📚 RAG EVIDENCE ({len(result.rag_evidence)} historical matches):")
        for i, ev in enumerate(result.rag_evidence, 1):
            print(f"  {i}. [{ev.stance.value.upper()}] {ev.source}")
        
        print(f"\n🔍 GAP ANALYSIS: {result.gap_analysis}")
        print(f"\n💭 REASONING:\n{result.reasoning}")
        print(f"\n📋 EXPLANATION:\n{result.final_explanation}")
        
    except Exception as e:
        print(f"\n✗ RAG pipeline failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("RAG PIPELINE TEST SUITE")
    print("=" * 80)
    
    # Check environment variables
    required_vars = ['GROQ_API_KEY', 'NEWS_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work correctly.")
        print("\nPlease set these variables in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_api_key_here")
        print()
    
    # Run tests
    try:
        # Test 1: Text analysis (doesn't require URL extraction)
        test_rag_pipeline_text()
        
        # Test 2: URL analysis (optional, requires valid URL)
        # Uncomment to test URL analysis:
        # test_rag_pipeline_url()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
