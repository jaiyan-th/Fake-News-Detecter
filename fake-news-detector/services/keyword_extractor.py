"""
Keyword extraction service using LLM
"""

import json
import re
from typing import List
from groq import Groq

class KeywordExtractor:
    """Service for extracting important keywords from articles using Mistral LLM"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API key is required")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"  # Use same model as other services
    
    def extract_keywords(self, content: str) -> List[str]:
        """
        Extract 5-7 important keywords from article content using Mistral LLM
        Focus on nouns, events, places, and people only
        Exclude common stop words and generic terms
        """
        if not content or len(content.strip()) < 50:
            return []
        
        try:
            # Use the exact prompt format from the blueprint
            prompt = f"""Extract 5–7 important keywords from this summary.
Rules:
Only nouns, events, places, people
No filler words
Output: ["keyword1", "keyword2"]

Summary: {content[:1000]}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON format first
            keywords = self._parse_json_keywords(result)
            
            # If JSON parsing fails, try line-by-line parsing
            if not keywords:
                keywords = self._parse_line_keywords(result)
            
            # Ensure we have 5-7 keywords
            keywords = self._validate_keyword_count(keywords)
            
            return keywords
            
        except Exception as e:
            print(f"LLM keyword extraction failed: {e}")
            # Fallback to simple extraction
            return self._simple_keyword_extraction(content)
    
    def _parse_json_keywords(self, result: str) -> List[str]:
        """Parse keywords from JSON format response"""
        try:
            # Look for JSON array in the response
            json_match = re.search(r'\[.*?\]', result)
            if json_match:
                json_str = json_match.group(0)
                keywords_list = json.loads(json_str)
                if isinstance(keywords_list, list):
                    return [str(kw).strip() for kw in keywords_list if str(kw).strip()]
        except (json.JSONDecodeError, AttributeError):
            pass
        return []
    
    def _parse_line_keywords(self, result: str) -> List[str]:
        """Parse keywords from line-by-line format"""
        keywords = []
        for line in result.strip().split('\n'):
            # Clean up the line
            keyword = line.strip().strip('-').strip('•').strip()
            keyword = re.sub(r'^\d+\.?\s*', '', keyword)  # Remove numbering
            keyword = keyword.strip('"').strip("'")  # Remove quotes
            
            if keyword and len(keyword) > 2 and not self._is_stop_word(keyword):
                keywords.append(keyword)
        
        return keywords
    
    def _validate_keyword_count(self, keywords: List[str]) -> List[str]:
        """Ensure keyword count is between 5-7"""
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                unique_keywords.append(kw)
                seen.add(kw_lower)
        
        # Ensure we have 5-7 keywords
        if len(unique_keywords) < 5:
            # Add generic fallback keywords if needed
            fallbacks = ['news', 'information', 'report', 'article', 'story']
            for fallback in fallbacks:
                if len(unique_keywords) >= 5:
                    break
                if fallback not in seen:
                    unique_keywords.append(fallback)
                    seen.add(fallback)
        elif len(unique_keywords) > 7:
            unique_keywords = unique_keywords[:7]
        
        return unique_keywords
    
    def _is_stop_word(self, word: str) -> bool:
        """Check if word is a common stop word or generic term"""
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'said', 'says', 'very', 'more', 'most',
            'also', 'just', 'only', 'even', 'back', 'any', 'some', 'no', 'not',
            'article', 'news', 'report', 'story', 'according', 'sources'
        }
        return word.lower() in stop_words
    
    def _simple_keyword_extraction(self, content: str) -> List[str]:
        """Fallback keyword extraction without LLM"""
        # Simple regex-based extraction focusing on proper nouns and important terms
        words = re.findall(r'\b[A-Z][a-zA-Z]+\b', content)
        
        # Filter out stop words and generic terms
        filtered_words = [word for word in words if not self._is_stop_word(word)]
        
        # Remove duplicates and take first 6
        unique_words = list(dict.fromkeys(filtered_words))[:6]
        
        # Ensure we have at least 5 keywords
        if len(unique_words) < 5:
            fallbacks = ['news', 'article', 'information', 'report', 'story']
            for fallback in fallbacks:
                if len(unique_words) >= 5:
                    break
                if fallback not in [w.lower() for w in unique_words]:
                    unique_words.append(fallback)
        
        # Ensure we have exactly 5-7 keywords
        if len(unique_words) > 7:
            unique_words = unique_words[:7]
        elif len(unique_words) < 5:
            # Add more fallbacks if needed
            additional_fallbacks = ['content', 'update', 'announcement', 'statement', 'development']
            for fallback in additional_fallbacks:
                if len(unique_words) >= 5:
                    break
                unique_words.append(fallback)
        
        return unique_words