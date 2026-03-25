"""
Contradiction detection service using LLM
"""

from typing import List, Dict
from groq import Groq
from services.extractor import ArticleContent

class ContradictionChecker:
    """Service for detecting contradictions between claims and articles"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API key is required")
        self.client = Groq(api_key=api_key)
        self.model = "mixtral-8x7b-32768"
    
    def check_contradictions(self, claims: List[str], articles: List[ArticleContent]) -> Dict:
        """
        Check for contradictions between claims and articles
        
        Returns:
            Dict with contradiction analysis results
        """
        if not claims or not articles:
            return {
                'contradiction_ratio': 0.0,
                'contradictions_found': [],
                'support_count': 0,
                'contradict_count': 0,
                'unrelated_count': 0
            }
        
        try:
            contradiction_results = []
            
            # Check each claim against top articles
            for claim in claims[:3]:  # Limit to top 3 claims
                for article in articles[:5]:  # Limit to top 5 articles
                    result = self._analyze_claim_article_relationship(claim, article)
                    contradiction_results.append(result)
            
            # Analyze results
            analysis = self._analyze_contradiction_results(contradiction_results)
            
            return analysis
            
        except Exception as e:
            print(f"Contradiction checking failed: {str(e)}")
            return {
                'contradiction_ratio': 0.0,
                'contradictions_found': [],
                'support_count': 0,
                'contradict_count': 0,
                'unrelated_count': 0
            }
    
    def _analyze_claim_article_relationship(self, claim: str, article: ArticleContent) -> Dict:
        """Analyze relationship between a single claim and article"""
        try:
            prompt = f"""
            Analyze the relationship between this CLAIM and ARTICLE content.
            
            CLAIM: {claim}
            
            ARTICLE: {article.title}
            {article.content[:800]}
            
            Classify the relationship as exactly one of:
            - SUPPORT: The article supports or confirms the claim
            - CONTRADICT: The article contradicts or disputes the claim  
            - UNRELATED: The article is unrelated to the claim
            
            Respond with only: SUPPORT, CONTRADICT, or UNRELATED
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            # Validate response
            if result not in ['SUPPORT', 'CONTRADICT', 'UNRELATED']:
                result = 'UNRELATED'
            
            return {
                'claim': claim,
                'article_url': article.url,
                'article_source': article.source,
                'relationship': result
            }
            
        except Exception as e:
            return {
                'claim': claim,
                'article_url': article.url,
                'article_source': article.source,
                'relationship': 'UNRELATED'
            }
    
    def _analyze_contradiction_results(self, results: List[Dict]) -> Dict:
        """Analyze overall contradiction patterns from individual results"""
        if not results:
            return {
                'contradiction_ratio': 0.0,
                'contradictions_found': [],
                'support_count': 0,
                'contradict_count': 0,
                'unrelated_count': 0
            }
        
        support_count = sum(1 for r in results if r['relationship'] == 'SUPPORT')
        contradict_count = sum(1 for r in results if r['relationship'] == 'CONTRADICT')
        unrelated_count = sum(1 for r in results if r['relationship'] == 'UNRELATED')
        
        total_relevant = support_count + contradict_count
        contradiction_ratio = contradict_count / total_relevant if total_relevant > 0 else 0.0
        
        # Extract specific contradictions
        contradictions_found = [
            {
                'claim': r['claim'],
                'source': r['article_source'],
                'url': r['article_url']
            }
            for r in results if r['relationship'] == 'CONTRADICT'
        ]
        
        return {
            'contradiction_ratio': contradiction_ratio,
            'contradictions_found': contradictions_found,
            'support_count': support_count,
            'contradict_count': contradict_count,
            'unrelated_count': unrelated_count
        }