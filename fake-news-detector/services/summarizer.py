"""
Article summarization service using Groq API with Llama and Mistral LLMs
Enhanced with multi-model support and intelligent fallback
"""

from typing import List, Tuple, Optional, Dict
from groq import Groq
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleSummarizer:
    """Service for summarizing articles and extracting key claims using multiple LLMs"""
    
    # Available models in priority order
    MODELS = [
        "llama-3.1-8b-instant",      # Primary: Fast and accurate
        "llama-3.3-70b-versatile",   # Secondary: Most powerful and reliable
        "llama-3.3-70b-versatile",   # Tertiary: Backup (same model for reliability)
    ]
    
    def __init__(self, api_key: str, timeout: int = 15, max_retries: int = 3):
        if not api_key:
            raise ValueError("Groq API key is required")
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise ValueError(f"Groq client initialization failed: {str(e)}")
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.current_model_index = 0
        self.preferred_model = None  # Allow setting a preferred model
    
    def set_preferred_model(self, model: str):
        """Set a preferred model to use first"""
        if model in self.MODELS:
            self.preferred_model = model
            logger.info(f"Preferred model set to: {model}")
        else:
            logger.warning(f"Model {model} not in available models list")
    
    def get_current_model(self) -> str:
        """Get the current model to use"""
        if self.preferred_model and self.current_model_index == 0:
            return self.preferred_model
        return self.MODELS[self.current_model_index % len(self.MODELS)]
    
    def try_next_model(self):
        """Switch to the next available model"""
        self.current_model_index += 1
        logger.info(f"Switching to model: {self.get_current_model()}")
    
    def summarize_article(self, content: str) -> Tuple[str, List[str]]:
        """
        Generate summary and extract key claims using ENSEMBLE of all models
        Combines results from multiple models for better accuracy
        
        Args:
            content: Article content to summarize
            
        Returns:
            Tuple of (summary, key_claims)
        """
        if not content or len(content.strip()) < 15:
            raise ValueError("Content too short for meaningful analysis. Please provide at least a full sentence.")
        
        # Truncate content to avoid token limits
        max_content_length = 4000
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            logger.info(f"Content truncated from {len(content)} to {max_content_length} characters")
        
        # Enhanced prompt for better results
        prompt = f"""You are an expert news analyst. Analyze the following article and provide:

1. A concise summary (3-4 sentences maximum)
2. Key factual claims (3-5 specific, verifiable statements)

Important:
- Focus on facts, not opinions
- Remove emotional language and exaggerations
- Be objective and precise
- Extract only verifiable claims

Format your response EXACTLY as:
Summary: [Your 3-4 sentence summary here]

Key Claims:
- [Claim 1]
- [Claim 2]
- [Claim 3]

Article:
{truncated_content}"""
        
        # Try to get results from all models
        all_summaries = []
        all_claims = []
        successful_models = []
        
        logger.info("Starting ensemble analysis with all models...")
        
        for model in self.MODELS:
            try:
                logger.info(f"Querying {model}...")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional news analyst specializing in fact extraction and summarization."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=600,
                    top_p=0.9,
                    timeout=self.timeout
                )
                
                result = response.choices[0].message.content
                summary, claims = self._parse_summary_response(result)
                
                if self._validate_results(summary, claims):
                    all_summaries.append(summary)
                    all_claims.extend(claims)
                    successful_models.append(model)
                    logger.info(f"✓ {model} completed successfully")
                else:
                    logger.warning(f"✗ {model} produced invalid results")
                    
            except Exception as e:
                logger.warning(f"✗ {model} failed: {str(e)}")
                continue
        
        # If we got at least one successful result, combine them
        if successful_models:
            logger.info(f"Ensemble complete: {len(successful_models)}/{len(self.MODELS)} models succeeded")
            
            # Combine summaries (use the longest/most detailed one)
            final_summary = max(all_summaries, key=len) if all_summaries else "Summary unavailable"
            
            # Combine and deduplicate claims
            final_claims = self._deduplicate_claims(all_claims)[:5]  # Top 5 unique claims
            
            return final_summary, final_claims
        
        # If all models failed, return fallback
        logger.error("All models failed in ensemble")
        return self._generate_fallback_summary(content)
    
    def _validate_results(self, summary: str, claims: List[str]) -> bool:
        """Validate that results meet quality standards"""
        if not summary or len(summary.strip()) < 20:
            return False
        
        if not claims or len(claims) < 1:
            return False
        
        # Check if claims are meaningful (not just error messages)
        meaningful_claims = [c for c in claims if len(c.strip()) > 15]
        if len(meaningful_claims) < 1:
            return False
        
        return True
    
    def _deduplicate_claims(self, claims: List[str]) -> List[str]:
        """Remove duplicate or very similar claims"""
        unique_claims = []
        
        for claim in claims:
            claim_lower = claim.lower().strip()
            
            # Check if this claim is too similar to existing ones
            is_duplicate = False
            for existing in unique_claims:
                existing_lower = existing.lower().strip()
                
                # Simple similarity check: if 70% of words match, consider duplicate
                claim_words = set(claim_lower.split())
                existing_words = set(existing_lower.split())
                
                if claim_words and existing_words:
                    overlap = len(claim_words & existing_words)
                    similarity = overlap / max(len(claim_words), len(existing_words))
                    
                    if similarity > 0.7:
                        is_duplicate = True
                        break
            
            if not is_duplicate and len(claim.strip()) > 15:
                unique_claims.append(claim)
        
        return unique_claims
    
    def _generate_fallback_summary(self, content: str) -> Tuple[str, List[str]]:
        """Generate basic summary when all LLM attempts fail"""
        logger.warning("Using fallback summary generation")
        
        # Extract first few sentences as summary
        sentences = [s.strip() + '.' for s in content.split('.') if len(s.strip()) > 20]
        summary = ' '.join(sentences[:3]) if sentences else "Unable to generate summary from content."
        
        # Extract some basic claims
        claims = sentences[3:6] if len(sentences) > 3 else ["Content analysis unavailable due to service limitations."]
        
        return summary, claims
    
    def _parse_summary_response(self, response: str) -> Tuple[str, List[str]]:
        """Parse the LLM response to extract summary and claims with improved error handling"""
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        summary = ""
        claims = []
        current_section = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect section headers
            if line_lower.startswith('summary:'):
                current_section = 'summary'
                summary_content = line[8:].strip()
                if summary_content:
                    summary = summary_content
                continue
            elif any(line_lower.startswith(prefix) for prefix in ['key claims:', 'claims:', 'factual claims:']):
                current_section = 'claims'
                continue
            
            # Skip empty lines
            if not line:
                continue
            
            # Process content based on section
            if current_section == 'summary':
                if summary:
                    summary += " " + line
                else:
                    summary = line
            elif current_section == 'claims':
                # Handle various claim formats
                claim_text = line
                for prefix in ['- ', '• ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ']:
                    if claim_text.startswith(prefix):
                        claim_text = claim_text[len(prefix):].strip()
                        break
                
                if claim_text and len(claim_text) > 10:
                    claims.append(claim_text)
        
        # Fallback parsing if structured format not found
        if not summary:
            # Look for the first substantial paragraph
            for line in lines:
                if len(line) > 30 and not any(keyword in line.lower() for keyword in ['summary:', 'claims:', 'key']):
                    summary = line
                    break
            
            if not summary:
                summary = ' '.join(lines[:3])
        
        if not claims:
            # Extract sentences that look like claims
            for line in lines:
                if (len(line) > 20 and 
                    not any(keyword in line.lower() for keyword in ['summary:', 'claims:', 'key', 'article:']) and
                    line not in summary):
                    claims.append(line)
                    if len(claims) >= 5:
                        break
        
        # Ensure we have valid results
        if not summary:
            summary = "Summary extraction failed."
        
        if not claims:
            claims = ["Unable to extract specific claims from the content."]
        
        return summary.strip(), claims[:5]  # Limit to 5 claims
    
    def extract_key_claims(self, content: str) -> List[str]:
        """
        Extract only factual claims from article content
        
        Args:
            content: Article content to analyze
            
        Returns:
            List of factual claims
        """
        try:
            _, claims = self.summarize_article(content)
            return claims
        except Exception as e:
            logger.error(f"Failed to extract claims: {e}")
            return ["Claim extraction failed due to service error."]
    
    def is_service_available(self) -> bool:
        """
        Check if the Groq API service is available
        
        Returns:
            True if service is available, False otherwise
        """
        for model in self.MODELS:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5,
                    timeout=5
                )
                logger.info(f"Service check passed with model: {model}")
                return True
            except Exception as e:
                logger.warning(f"Service check failed for {model}: {str(e)}")
                continue
        
        logger.error("All models unavailable")
        return False
