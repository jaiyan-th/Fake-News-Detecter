"""
Enhanced decision engine with credibility assessment and LLM explanation generation (Phase 4)
"""

from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
import json

class Verdict(Enum):
    REAL = "REAL"
    FAKE = "FAKE"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class AnalysisResult:
    verdict: Verdict
    confidence: float
    explanation: str
    matched_articles: List[Dict]
    summary: str
    key_claims: List[str]
    processing_time: float = 0.0

class DecisionEngine:
    """Enhanced decision engine with credibility assessment, contradiction detection, and multi-model LLM explanations"""
    
    # Available models for explanation generation
    MODELS = [
        "llama-3.1-8b-instant",      # Primary: Fast and accurate
        "llama-3.2-90b-text-preview", # Secondary: Llama 3.2, very powerful
        "llama-3.3-70b-versatile",   # Tertiary: Most powerful
    ]
    
    def __init__(self, groq_api_key: str = None):
        """Initialize enhanced decision engine with all services"""
        # Import here to avoid circular imports
        from services.credibility import CredibilityAssessor
        from services.contradiction_checker import ContradictionChecker
        from groq import Groq
        import logging
        
        self.logger = logging.getLogger(__name__)
        self.credibility_assessor = CredibilityAssessor()
        
        # Initialize Groq client for LLM explanations
        self.groq_client = None
        self.current_model_index = 0
        self.preferred_model = None  # Allow setting a preferred model
        
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
                self.logger.info("Decision engine Groq client initialized")
            except Exception as e:
                self.logger.error(f"Groq client initialization failed: {e}")
                self.groq_client = None
        
        # Initialize contradiction checker if API key is provided
        self.contradiction_checker = None
        if groq_api_key:
            try:
                self.contradiction_checker = ContradictionChecker(groq_api_key)
            except Exception as e:
                self.logger.warning(f"ContradictionChecker initialization failed: {e}")
                self.contradiction_checker = None
    
    def set_preferred_model(self, model: str):
        """Set a preferred model to use first"""
        if model in self.MODELS:
            self.preferred_model = model
            self.logger.info(f"Decision engine preferred model set to: {model}")
        else:
            self.logger.warning(f"Model {model} not in available models list")
    
    def get_current_model(self) -> str:
        """Get the current model to use"""
        if self.preferred_model and self.current_model_index == 0:
            return self.preferred_model
        return self.MODELS[self.current_model_index % len(self.MODELS)]
    
    def try_next_model(self):
        """Switch to the next available model"""
        self.current_model_index += 1
        self.logger.info(f"Switching to model: {self.get_current_model()}")
    
    def make_decision(self, similarity_scores, summary: str, 
                     claims: List[str], related_articles=None, pattern_result=None, 
                     input_source: str = "") -> AnalysisResult:
        """
        Make final verdict decision based on credibility assessment and contradiction detection
        
        Enhanced Decision Rules (Phase 4):
        - if input_source is trusted AND high similarity → REAL (boost confidence)
        - if contradiction_ratio > 0.5 → FAKE (override rule)
        - elif trusted_support ≥ 3 → REAL
        - elif trusted_support == 0 → FAKE
        - else → UNCERTAIN
        
        Confidence Calculation:
        confidence = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        (adjusted for contradiction factor and input source trust)
        """
        try:
            # Handle edge case: empty results
            if not similarity_scores:
                return self._create_result(
                    Verdict.UNCERTAIN, 0.2, 
                    "No similar articles found to verify claims.",
                    [], summary, claims
                )
            
            # Check if input source is trusted
            input_is_trusted = self._is_input_source_trusted(input_source)
            
            # Assess credibility using CredibilityAssessor
            credibility_data = self.credibility_assessor.assess_credibility(similarity_scores)
            
            # Check for contradictions if service is available and we have related articles
            contradiction_data = None
            if self.contradiction_checker and related_articles and claims:
                try:
                    # Convert related articles to proper format for contradiction checker
                    article_contents = []
                    for article in related_articles[:5]:  # Limit to top 5 for performance
                        if hasattr(article, 'content'):
                            article_contents.append(article)
                        else:
                            # Handle case where related_articles might be dict format
                            from services.extractor import ArticleContent
                            article_content = ArticleContent(
                                title=article.get('title', ''),
                                content=article.get('content', ''),
                                url=article.get('url', ''),
                                source=article.get('source', ''),
                                published_date=article.get('published_date')
                            )
                            article_contents.append(article_content)
                    
                    contradiction_data = self.contradiction_checker.check_contradictions(
                        claims[:3], article_contents  # Limit claims to top 3 for performance
                    )
                except Exception as e:
                    print(f"Contradiction checking failed: {e}")
                    contradiction_data = None
            
            # Apply enhanced decision rules with contradiction detection and pattern analysis
            verdict, confidence = self._apply_enhanced_rules_with_contradictions_and_patterns(
                credibility_data, contradiction_data, pattern_result, input_is_trusted
            )
            
            # Generate comprehensive explanation using LLM
            explanation = self._generate_comprehensive_explanation(
                verdict, confidence, credibility_data, similarity_scores, contradiction_data, 
                summary, claims, pattern_result, input_source
            )
            
            # Format matched articles (top 3)
            matched_articles = self._format_matched_articles(similarity_scores[:3])
            
            return self._create_result(
                verdict, confidence, explanation, matched_articles, summary, claims
            )
            
        except Exception as e:
            # Handle edge case: processing error
            return self._create_result(
                Verdict.UNCERTAIN, 0.1,
                f"Analysis error occurred: {str(e)}",
                [], summary, claims
            )
    
    def _is_input_source_trusted(self, source: str) -> bool:
        """Check if the input source itself is from a trusted organization"""
        if not source:
            return False
        
        # Map of domain patterns to trusted source names
        trusted_domains = {
            'bbc.co.uk': 'bbc',
            'bbc.com': 'bbc',
            'reuters.com': 'reuters',
            'apnews.com': 'associated press',
            'cnn.com': 'cnn',
            'npr.org': 'npr',
            'theguardian.com': 'the guardian',
            'nytimes.com': 'new york times',
            'washingtonpost.com': 'washington post',
            'wsj.com': 'wall street journal',
            'bloomberg.com': 'bloomberg',
            'thehindu.com': 'the hindu',
            'ndtv.com': 'ndtv',
            'timesofindia.indiatimes.com': 'times of india',
            'indiatimes.com': 'times of india',
            'indianexpress.com': 'indian express',
            'hindustantimes.com': 'hindustan times',
            'theprint.in': 'the print',
            'scroll.in': 'scroll',
            'thequint.com': 'the quint',
            'moneycontrol.com': 'moneycontrol',
            'indiatoday.in': 'india today',
            'news18.com': 'news18',
            'firstpost.com': 'firstpost',
            'deccanherald.com': 'deccan herald',
            'telegraphindia.com': 'telegraph',
            'tribuneindia.com': 'tribune',
            'livemint.com': 'mint',
            'economictimes.indiatimes.com': 'economic times',
            'aljazeera.com': 'al jazeera',
            'france24.com': 'france 24',
            'dw.com': 'dw',
            'pbs.org': 'pbs',
            'abcnews.go.com': 'abc news',
            'cbsnews.com': 'cbs news',
            'nbcnews.com': 'nbc news',
            'ft.com': 'financial times'
        }
        
        # Also keep the original keyword-based matching for text sources
        trusted_keywords = {
            'bbc', 'reuters', 'associated press', 'cnn', 'npr',
            'the guardian', 'new york times', 'washington post',
            'wall street journal', 'bloomberg', 'the hindu', 'ndtv',
            'times of india', 'indian express', 'hindustan times',
            'the print', 'scroll', 'the quint', 'moneycontrol',
            'india today', 'news18', 'firstpost', 'deccan herald',
            'telegraph', 'tribune', 'mint', 'livemint', 'economic times',
            'al jazeera', 'france 24', 'dw', 'pbs', 'abc news', 'cbs news',
            'nbc news', 'financial times', 'pti', 'ani', 'ians'
        }
        
        source_lower = source.lower()
        
        # Check domain-based matching first (more precise)
        for domain, name in trusted_domains.items():
            if domain in source_lower:
                return True
        
        # Fallback to keyword matching (for text sources)
        return any(trusted in source_lower for trusted in trusted_keywords)
    
    def _apply_enhanced_rules_with_contradictions(self, credibility_data: Dict, 
                                                contradiction_data: Dict = None) -> tuple:
        """Apply enhanced decision rules with credibility assessment and contradiction detection"""
        
        trusted_support = credibility_data['trusted_matches']
        avg_similarity = credibility_data['avg_similarity']
        trusted_ratio = credibility_data['trusted_ratio']
        support_ratio = credibility_data['support_ratio']
        
        # Calculate contradiction factor for confidence adjustment
        contradiction_factor = 0.0
        if contradiction_data:
            contradiction_ratio = contradiction_data.get('contradiction_ratio', 0)
            contradict_count = contradiction_data.get('contradict_count', 0)
            # Use contradiction ratio as the primary factor, with count as secondary
            contradiction_factor = min(contradiction_ratio + (contradict_count * 0.1), 1.0)
        
        # Check for contradiction override rule first (highest priority)
        if contradiction_data and contradiction_data.get('contradiction_ratio', 0) > 0.5:
            # Contradiction Override Rule: contradiction_ratio > 0.5 → FAKE
            confidence = self._calculate_confidence(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor
            )
            # Additional confidence reduction for strong contradictions
            confidence = max(0.1, confidence - 0.2)
            return Verdict.FAKE, confidence
        
        # Enhanced Rule 1: trusted_support ≥ 3 → REAL
        if trusted_support >= 3:
            # Calculate confidence using multi-factor formula with contradiction adjustment
            confidence = self._calculate_confidence(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor
            )
            # Boost confidence for strong trusted support
            confidence = min(0.95, confidence + 0.1)
            return Verdict.REAL, confidence
        
        # Enhanced Rule 2: trusted_support == 0 → FAKE
        elif trusted_support == 0:
            # Calculate base confidence and reduce for lack of trusted sources
            confidence = self._calculate_confidence(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor
            )
            confidence = max(0.1, confidence - 0.2)  # Reduce confidence for no trusted sources
            return Verdict.FAKE, confidence
        
        # Enhanced Rule 3: Some trusted support but not enough → UNCERTAIN
        else:
            # Calculate confidence using standard formula with contradiction adjustment
            confidence = self._calculate_confidence(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor
            )
            return Verdict.UNCERTAIN, confidence
    
    def _apply_enhanced_rules_with_contradictions_and_patterns(self, credibility_data: Dict, 
                                                             contradiction_data: Dict = None,
                                                             pattern_result = None,
                                                             input_is_trusted: bool = False) -> tuple:
        """Apply enhanced decision rules with credibility assessment, contradiction detection, pattern analysis, and input source trust"""
        
        trusted_support = credibility_data['trusted_matches']
        avg_similarity = credibility_data['avg_similarity']
        trusted_ratio = credibility_data['trusted_ratio']
        support_ratio = credibility_data['support_ratio']
        
        # Calculate contradiction factor for confidence adjustment
        contradiction_factor = 0.0
        if contradiction_data:
            contradiction_ratio = contradiction_data.get('contradiction_ratio', 0)
            contradict_count = contradiction_data.get('contradict_count', 0)
            # Use contradiction ratio as the primary factor, with count as secondary
            contradiction_factor = min(contradiction_ratio + (contradict_count * 0.1), 1.0)
        
        # Calculate pattern factor for confidence adjustment
        pattern_factor = 0.0
        if pattern_result:
            pattern_score = pattern_result.overall_score
            # High pattern score (>0.5) suggests fake news characteristics
            if pattern_score > 0.5:
                pattern_factor = pattern_score * 0.3  # Reduce confidence
            elif pattern_score > 0.3:
                pattern_factor = pattern_score * 0.2  # Moderate reduction
        
        # NEW: Input source trust boost - EVEN IF NO SIMILAR ARTICLES FOUND
        # If the input itself is from a trusted source, give it credibility
        if input_is_trusted:
            # Check if we have similar articles
            if avg_similarity > 0.4:
                # Input from trusted source with decent similarity → likely REAL
                confidence = self._calculate_confidence_with_patterns(
                    avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
                )
                # Boost confidence for trusted input source
                confidence = min(0.95, confidence + 0.15)
                
                # Check for contradictions - even trusted sources can be wrong
                if contradiction_data and contradiction_data.get('contradiction_ratio', 0) > 0.5:
                    confidence = max(0.3, confidence - 0.3)
                    return Verdict.UNCERTAIN, confidence
                
                return Verdict.REAL, confidence
            
            elif avg_similarity == 0:
                # Trusted source but no similar articles found
                # This could be breaking news or niche topic
                # Give moderate confidence based on source trust alone
                base_confidence = 0.65  # Start with moderate confidence
                
                # Adjust for patterns if detected
                if pattern_result and pattern_result.overall_score > 0.5:
                    # High fake news patterns - reduce confidence significantly
                    base_confidence = max(0.3, base_confidence - 0.35)
                    return Verdict.UNCERTAIN, base_confidence
                elif pattern_result and pattern_result.overall_score > 0.3:
                    # Moderate patterns - slight reduction
                    base_confidence = max(0.5, base_confidence - 0.15)
                
                # No contradictions possible without similar articles
                # Trust the source
                return Verdict.REAL, base_confidence
        
        # Check for pattern override rule (high fake news patterns → FAKE)
        if pattern_result and pattern_result.overall_score > 0.6:
            # Pattern Override Rule: high pattern score → FAKE
            confidence = self._calculate_confidence_with_patterns(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
            )
            confidence = max(0.1, confidence - 0.1)  # Additional reduction for strong patterns
            return Verdict.FAKE, confidence
        
        # Check for contradiction override rule first (highest priority)
        if contradiction_data and contradiction_data.get('contradiction_ratio', 0) > 0.5:
            # Contradiction Override Rule: contradiction_ratio > 0.5 → FAKE
            confidence = self._calculate_confidence_with_patterns(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
            )
            # Additional confidence reduction for strong contradictions
            confidence = max(0.1, confidence - 0.2)
            return Verdict.FAKE, confidence
        
        # Enhanced Rule 1: trusted_support >= 1 AND good similarity → REAL (but consider patterns)
        if trusted_support >= 1:
            # Calculate confidence using multi-factor formula with pattern adjustment
            confidence = self._calculate_confidence_with_patterns(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
            )
            
            # If patterns strongly suggest fake news, downgrade to UNCERTAIN
            if pattern_result and pattern_result.overall_score > 0.5:
                confidence = max(0.1, confidence - 0.3)
                return Verdict.UNCERTAIN, confidence
            
            # Check if similarity is too low (< 0.35) - might be unrelated articles
            elif avg_similarity < 0.35:
                # Low similarity despite trusted sources - likely unrelated articles
                confidence = max(0.2, confidence - 0.2)
                return Verdict.UNCERTAIN, confidence
            
            # Check if similarity is moderate (0.35-0.50) - weak match
            elif avg_similarity < 0.50:
                # Moderate similarity - reduce confidence but still REAL
                confidence = max(0.3, confidence - 0.1)
                return Verdict.REAL, confidence
            
            else:
                # Good similarity (>= 0.50) with trusted sources - strong REAL
                # Boost confidence for strong trusted support
                confidence = min(0.95, confidence + (0.1 * trusted_support))
                return Verdict.REAL, confidence
        
        # Enhanced Rule 2: trusted_support == 0 → UNCERTAIN or FAKE (depending on patterns)
        elif trusted_support == 0:
            # Calculate base confidence and reduce for lack of trusted sources
            confidence = self._calculate_confidence_with_patterns(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
            )
            confidence = max(0.1, confidence - 0.2)  # Reduce confidence for no trusted sources
            
            # If patterns also suggest fake news, increase confidence in FAKE verdict
            if pattern_result and pattern_result.overall_score > 0.4:
                confidence = min(0.9, confidence + 0.1)
                return Verdict.FAKE, confidence
            
            # Otherwise, it's just unverified, not necessarily FAKE
            return Verdict.UNCERTAIN, confidence
        
        # Enhanced Rule 3: Some trusted support but not enough → UNCERTAIN (consider patterns)
        else:
            # Calculate confidence using standard formula with pattern adjustment
            confidence = self._calculate_confidence_with_patterns(
                avg_similarity, trusted_ratio, support_ratio, contradiction_factor, pattern_factor
            )
            
            # If patterns strongly suggest fake news, lean towards FAKE
            if pattern_result and pattern_result.overall_score > 0.5:
                return Verdict.FAKE, max(0.1, confidence - 0.1)
            
            return Verdict.UNCERTAIN, confidence
    
    def _apply_enhanced_rules(self, credibility_data: Dict) -> tuple:
        """Apply enhanced decision rules with credibility assessment"""
        
        trusted_support = credibility_data['trusted_matches']
        avg_similarity = credibility_data['avg_similarity']
        trusted_ratio = credibility_data['trusted_ratio']
        support_ratio = credibility_data['support_ratio']
        
        # Enhanced Rule 1: trusted_support >= 1 → REAL
        if trusted_support >= 1:
            # Calculate confidence using multi-factor formula
            confidence = self._calculate_confidence(avg_similarity, trusted_ratio, support_ratio)
            # Boost confidence for strong trusted support
            confidence = min(0.95, confidence + (0.1 * trusted_support))
            return Verdict.REAL, confidence
        
        # Enhanced Rule 2: trusted_support == 0 → UNCERTAIN
        elif trusted_support == 0:
            # Calculate base confidence and reduce for lack of trusted sources
            confidence = self._calculate_confidence(avg_similarity, trusted_ratio, support_ratio)
            confidence = max(0.1, confidence - 0.2)  # Reduce confidence for no trusted sources
            return Verdict.UNCERTAIN, confidence
        
        # Enhanced Rule 3: Catch-all → UNCERTAIN
        else:
            # Calculate confidence using standard formula
            confidence = self._calculate_confidence(avg_similarity, trusted_ratio, support_ratio)
            return Verdict.UNCERTAIN, confidence
    
    def _calculate_confidence(self, avg_similarity: float, trusted_ratio: float, 
                            support_ratio: float, contradiction_factor: float = 0.0) -> float:
        """
        Calculate confidence using multi-factor formula with contradiction adjustment:
        base_confidence = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        final_confidence = base_confidence * (1.0 - contradiction_factor)
        """
        # Calculate base confidence using the standard formula
        base_confidence = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        
        # Apply contradiction factor to reduce confidence when contradictions are found
        # contradiction_factor should be between 0.0 (no contradictions) and 1.0 (maximum contradictions)
        final_confidence = base_confidence * (1.0 - min(contradiction_factor, 0.8))  # Cap reduction at 80%
        
        # Ensure confidence is between 0.0 and 1.0
        return max(0.0, min(1.0, final_confidence))
    
    def _calculate_confidence_with_patterns(self, avg_similarity: float, trusted_ratio: float, 
                                          support_ratio: float, contradiction_factor: float = 0.0,
                                          pattern_factor: float = 0.0) -> float:
        """
        Calculate confidence using multi-factor formula with pattern analysis:
        base_confidence = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        final_confidence = base_confidence * (1.0 - contradiction_factor) * (1.0 - pattern_factor)
        """
        # Calculate base confidence using the standard formula
        base_confidence = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        
        # Apply contradiction factor to reduce confidence when contradictions are found
        contradiction_adjustment = 1.0 - min(contradiction_factor, 0.8)  # Cap reduction at 80%
        
        # Apply pattern factor to reduce confidence when fake news patterns are found
        pattern_adjustment = 1.0 - min(pattern_factor, 0.6)  # Cap reduction at 60%
        
        # Combine all adjustments
        final_confidence = base_confidence * contradiction_adjustment * pattern_adjustment
        
        # Ensure confidence is between 0.0 and 1.0
        return max(0.0, min(1.0, final_confidence))
    
    def _generate_comprehensive_explanation(self, verdict: Verdict, confidence: float, 
                                          credibility_data: Dict, similarity_scores, 
                                          contradiction_data: Dict = None, summary: str = "", 
                                          claims: List[str] = None, pattern_result = None,
                                          input_source: str = "") -> str:
        """Generate comprehensive explanation using LLM with fallback to rule-based explanation"""
        
        # Try LLM-powered explanation first
        if self.groq_client:
            try:
                llm_explanation = self._generate_llm_explanation(
                    verdict, confidence, credibility_data, similarity_scores, 
                    contradiction_data, summary, claims, pattern_result, input_source
                )
                if llm_explanation:
                    return llm_explanation
            except Exception as e:
                print(f"LLM explanation generation failed: {e}")
        
        # Fallback to enhanced rule-based explanation
        return self._generate_enhanced_explanation(
            verdict, credibility_data, similarity_scores, contradiction_data, pattern_result, input_source
        )
    
    def _generate_llm_explanation(self, verdict: Verdict, confidence: float,
                                credibility_data: Dict, similarity_scores,
                                contradiction_data: Dict = None, summary: str = "",
                                claims: List[str] = None, pattern_result = None,
                                input_source: str = "") -> Optional[str]:
        """Generate explanation using LLM with multi-model fallback and enhanced error handling"""
        
        # Prepare analysis data for LLM
        trusted_matches = credibility_data.get('trusted_matches', 0)
        avg_similarity = credibility_data.get('avg_similarity', 0.0)
        total_articles = credibility_data.get('total_articles', 0)
        
        # Get trusted sources
        trusted_sources = [score.source for score in similarity_scores[:3] if score.is_trusted]
        
        # Add input source information
        input_source_info = ""
        if input_source:
            input_source_info = f"\n- Input Source: {input_source} (detected from content)"
        
        # Prepare contradiction information
        contradiction_info = "None"
        if contradiction_data:
            contradict_count = contradiction_data.get('contradict_count', 0)
            support_count = contradiction_data.get('support_count', 0)
            contradiction_ratio = contradiction_data.get('contradiction_ratio', 0)
            
            if contradict_count > 0 or support_count > 0:
                contradiction_info = f"{support_count} supporting, {contradict_count} contradicting (ratio: {contradiction_ratio:.1%})"
        
        # Prepare pattern information
        pattern_info = "None detected"
        if pattern_result:
            pattern_score = pattern_result.overall_score
            patterns_count = len(pattern_result.patterns_detected)
            if pattern_score > 0.1:
                pattern_info = f"Score: {pattern_score:.1%}, {patterns_count} patterns detected"
                if pattern_result.emotional_indicators:
                    pattern_info += f" (emotional: {len(pattern_result.emotional_indicators)})"
                if pattern_result.suspicious_phrases:
                    pattern_info += f" (suspicious: {len(pattern_result.suspicious_phrases)})"
        
        # Create enhanced structured prompt
        prompt = f"""You are an expert fact-checker analyzing news content for authenticity.

News Content Summary:
{summary[:400] if summary else 'Not available'}

Key Claims Being Verified:
{', '.join(claims[:3]) if claims else 'None extracted'}

Verification Analysis:{input_source_info}
- Similarity: Average {avg_similarity:.1%} across {total_articles} articles
- Trusted Sources: {trusted_matches} matches from {', '.join(trusted_sources[:3]) if trusted_sources else 'None'}
- Contradictions: {contradiction_info}
- Fake News Patterns: {pattern_info}

Verdict: {verdict.value} (Confidence: {confidence:.0%})

Task: Write a clear, professional explanation (2-3 sentences) that:
1. FIRST briefly describes what the news is about (the main event/topic)
2. THEN explains why this verdict was reached based on the verification evidence
3. Be specific about the news content, not just the metrics

Example format: "This article reports about [main topic/event]. The verdict of {verdict.value} is based on [key evidence]. [Additional supporting detail]."

Start directly with the explanation, no labels or prefixes."""

        # Try each model with retries
        models_tried = []
        last_error = None
        
        for model_attempt in range(len(self.MODELS)):
            current_model = self.get_current_model()
            models_tried.append(current_model)
            
            for retry in range(2):  # 2 retries per model
                try:
                    self.logger.info(f"Generating explanation with {current_model} (attempt {retry + 1})")
                    
                    response = self.groq_client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional fact-checker providing clear, evidence-based explanations."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.3,
                        max_tokens=200,
                        top_p=0.9,
                        timeout=10
                    )
                    
                    explanation = response.choices[0].message.content.strip()
                    
                    # Validate explanation quality
                    if len(explanation) > 30 and not explanation.lower().startswith(('error', 'i cannot', 'i apologize')):
                        self.logger.info(f"Explanation generated successfully with {current_model}")
                        return explanation
                    else:
                        self.logger.warning(f"Low quality explanation from {current_model}, retrying...")
                        continue
                    
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"Explanation generation failed with {current_model}: {str(e)}")
                    
                    if retry < 1:
                        import time
                        time.sleep(1)
                        continue
            
            # Try next model
            self.try_next_model()
        
        # All models failed
        self.logger.error(f"All models failed for explanation generation: {models_tried}")
        return None
    
    def _generate_enhanced_explanation(self, verdict: Verdict, credibility_data: Dict,
                                     similarity_scores, contradiction_data: Dict = None, 
                                     pattern_result = None, input_source: str = "") -> str:
        """Generate enhanced human-readable explanation with credibility factors and contradictions"""
        
        trusted_support = credibility_data['trusted_matches']
        total_articles = credibility_data['total_articles']
        avg_similarity = credibility_data['avg_similarity']
        high_similarity_count = credibility_data['high_similarity_count']
        
        # Count trusted sources in top matches
        trusted_sources = [score.source for score in similarity_scores[:5] if score.is_trusted]
        
        # Check if input source is trusted
        input_is_trusted = self._is_input_source_trusted(input_source)
        
        # Add input source information
        input_source_prefix = ""
        if input_source:
            if input_is_trusted:
                input_source_prefix = f"Article from trusted source {input_source}. "
            else:
                input_source_prefix = f"Content from {input_source}. "
        
        # Add contradiction information if available
        contradiction_info = ""
        if contradiction_data:
            contradict_count = contradiction_data.get('contradict_count', 0)
            support_count = contradiction_data.get('support_count', 0)
            contradiction_ratio = contradiction_data.get('contradiction_ratio', 0)
            contradictions_found = contradiction_data.get('contradictions_found', [])
            
            if contradict_count > 0:
                contradiction_info = f" Found {contradict_count} contradicting articles"
                if support_count > 0:
                    contradiction_info += f" vs {support_count} supporting"
                if contradiction_ratio > 0.3:
                    contradiction_info += f" (ratio: {contradiction_ratio:.1%})"
                if contradictions_found:
                    sources = [c['source'] for c in contradictions_found[:2]]
                    contradiction_info += f" from {', '.join(sources)}"
                contradiction_info += "."
            elif support_count > 0:
                contradiction_info = f" {support_count} supporting articles found with no contradictions."
        
        # Add pattern information if available
        pattern_info = ""
        if pattern_result and pattern_result.overall_score > 0.1:
            pattern_score = pattern_result.overall_score
            
            if pattern_score > 0.5:
                pattern_info = f" High fake news indicators detected (score: {pattern_score:.1%})"
            elif pattern_score > 0.3:
                pattern_info = f" Moderate fake news indicators detected (score: {pattern_score:.1%})"
            else:
                pattern_info = f" Low fake news indicators (score: {pattern_score:.1%})"
            
            if pattern_result.emotional_indicators:
                pattern_info += f" including emotional language"
            if pattern_result.suspicious_phrases:
                pattern_info += f" and suspicious phrases"
            pattern_info += "."
        
        # Special case: Trusted source but no similar articles found
        if input_is_trusted and total_articles == 0:
            if verdict == Verdict.REAL:
                explanation = input_source_prefix + "No similar articles found for cross-verification, but the source is a trusted news organization with established credibility."
                if pattern_info:
                    explanation += pattern_info
                return explanation
            elif verdict == Verdict.UNCERTAIN:
                explanation = input_source_prefix + "No similar articles found for cross-verification. While the source has some credibility concerns"
                if pattern_info:
                    explanation += f", {pattern_info.lower()}"
                explanation += ", more evidence is needed for a definitive verdict."
                return explanation
        
        if verdict == Verdict.REAL:
            explanation = input_source_prefix + (f"Verified as REAL with {trusted_support} trusted source matches "
                         f"from {total_articles} articles analyzed. ")
            if trusted_sources:
                explanation += f"Trusted sources: {', '.join(trusted_sources[:3])}. "
            explanation += f"Similarity: {avg_similarity:.1%}, High matches: {high_similarity_count}."
            if contradiction_info:
                explanation += contradiction_info
            if pattern_info:
                explanation += pattern_info
            
        elif verdict == Verdict.FAKE:
            if pattern_result and pattern_result.overall_score > 0.6:
                explanation = input_source_prefix + (f"Flagged as FAKE due to strong fake news patterns.{pattern_info} ")
                explanation += f"Similarity: {avg_similarity:.1%}."
                if contradiction_info:
                    explanation += contradiction_info
            elif contradiction_data and contradiction_data.get('contradiction_ratio', 0) > 0.5:
                explanation = input_source_prefix + (f"Flagged as FAKE due to significant contradictions "
                             f"in related articles.{contradiction_info} ")
                explanation += f"Similarity: {avg_similarity:.1%}."
                if pattern_info:
                    explanation += pattern_info
            elif trusted_support == 0:
                explanation = input_source_prefix + (f"Flagged as FAKE with NO trusted source matches "
                             f"from {total_articles} articles analyzed. ")
                explanation += f"Similarity: {avg_similarity:.1%}, High matches: {high_similarity_count}."
                if contradiction_info:
                    explanation += contradiction_info
                if pattern_info:
                    explanation += pattern_info
            else:
                explanation = input_source_prefix + (f"Flagged as FAKE despite some matches "
                             f"({trusted_support} trusted sources). ")
                explanation += f"Similarity: {avg_similarity:.1%}, High matches: {high_similarity_count}."
                if contradiction_info:
                    explanation += contradiction_info
                if pattern_info:
                    explanation += pattern_info
            
        else:  # UNCERTAIN
            explanation = input_source_prefix + (f"Verdict UNCERTAIN with {trusted_support} trusted source matches "
                         f"from {total_articles} articles analyzed. ")
            if trusted_sources:
                explanation += f"Some trusted sources: {', '.join(trusted_sources[:2])}. "
            explanation += f"Similarity: {avg_similarity:.1%}, needs more evidence for definitive verdict."
            if contradiction_info:
                explanation += contradiction_info
            if pattern_info:
                explanation += pattern_info
        
        return explanation
    
    def _format_matched_articles(self, top_scores) -> List[Dict]:
        """Format top similarity scores as matched articles"""
        matched_articles = []
        
        for score in top_scores:
            article_dict = {
                'url': score.article_url,
                'title': score.article_title,
                'source': score.source,
                'similarity': f"{score.score:.1%}",
                'is_trusted': score.is_trusted
            }
            matched_articles.append(article_dict)
        
        return matched_articles
    
    def _create_result(self, verdict: Verdict, confidence: float, explanation: str,
                      matched_articles: List[Dict], summary: str, claims: List[str]) -> AnalysisResult:
        """Create AnalysisResult with proper confidence bounds"""
        
        # Ensure confidence is between 0.0 and 1.0
        confidence = max(0.0, min(1.0, confidence))
        
        return AnalysisResult(
            verdict=verdict,
            confidence=confidence,
            explanation=explanation,
            matched_articles=matched_articles,
            summary=summary,
            key_claims=claims
        )