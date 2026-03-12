"""
Module 6: Result Dashboard
Formats and presents results with detailed analysis
"""

from typing import Dict, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultDashboard:
    """Formats analysis results for presentation"""
    
    @staticmethod
    def format_analysis_result(article: Dict, prediction_result: Dict, 
                               verification_result: Dict) -> Dict:
        """
        Format complete analysis result for dashboard display
        
        Args:
            article: Original article data
            prediction_result: ML model prediction results
            verification_result: Verification layer results
            
        Returns:
            Formatted dashboard data
        """
        # Extract key information
        prediction = prediction_result.get('prediction', 'UNKNOWN')
        confidence = prediction_result.get('confidence', 0.0)
        
        # Build dashboard result
        dashboard_result = {
            'timestamp': datetime.now().isoformat(),
            'article_info': {
                'title': article.get('title', 'No title'),
                'source': article.get('source', 'Unknown'),
                'author': article.get('author', 'Unknown'),
                'url': article.get('url', ''),
            },
            'classification': {
                'status': prediction,
                'confidence_score': confidence,
                'confidence_percentage': f"{confidence * 100:.1f}%",
                'confidence_level': ResultDashboard._get_confidence_level(confidence),
            },
            'analysis_details': {
                'model_type': prediction_result.get('model_type', 'Unknown'),
                'interpretation': prediction_result.get('interpretation', ''),
                'feature_signals': prediction_result.get('feature_signals', []),
            },
            'sentiment_analysis': prediction_result.get('sentiment_analysis', {}),
            'source_verification': verification_result.get('source_verification', {}),
            'fact_check': verification_result.get('fact_check', {}),
            'final_verdict': verification_result.get('final_verdict', {}),
            'recommendations': ResultDashboard._generate_recommendations(
                prediction, confidence, verification_result
            ),
            'visual_indicators': ResultDashboard._generate_visual_indicators(
                prediction, confidence
            )
        }
        
        return dashboard_result
    
    @staticmethod
    def _get_confidence_level(confidence: float) -> str:
        """Convert confidence score to level"""
        if confidence > 0.9:
            return "Very High"
        elif confidence > 0.75:
            return "High"
        elif confidence > 0.6:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def _generate_recommendations(prediction: str, confidence: float, 
                                  verification: Dict) -> List[str]:
        """Generate user recommendations based on analysis"""
        recommendations = []
        
        if prediction == "FAKE":
            recommendations.append("⚠️ Exercise caution before sharing this article")
            recommendations.append("🔍 Verify claims with trusted news sources")
            recommendations.append("📊 Check the source's credibility and history")
            
            if confidence > 0.8:
                recommendations.append("🚫 Strong indicators suggest this is fake news")
        else:
            recommendations.append("✓ Article appears credible based on analysis")
            
            if confidence < 0.7:
                recommendations.append("⚠️ Still verify important claims independently")
        
        # Source-based recommendations
        source_check = verification.get('source_verification', {})
        if source_check.get('status') == 'unreliable':
            recommendations.append("⚠️ Source has low credibility rating")
        elif source_check.get('status') == 'trusted':
            recommendations.append("✓ Source is a trusted news organization")
        
        return recommendations
    
    @staticmethod
    def _generate_visual_indicators(prediction: str, confidence: float) -> Dict:
        """Generate visual indicators for UI"""
        if prediction == "FAKE":
            if confidence > 0.8:
                color = "#dc3545"  # Red
                icon = "🚫"
                status_text = "FAKE NEWS"
            else:
                color = "#fd7e14"  # Orange
                icon = "⚠️"
                status_text = "LIKELY FAKE"
        else:
            if confidence > 0.8:
                color = "#28a745"  # Green
                icon = "✓"
                status_text = "REAL NEWS"
            else:
                color = "#ffc107"  # Yellow
                icon = "ℹ️"
                status_text = "LIKELY REAL"
        
        return {
            'color': color,
            'icon': icon,
            'status_text': status_text,
            'confidence_bar_width': f"{confidence * 100}%"
        }
    
    @staticmethod
    def format_summary_statistics(analyses: List[Dict]) -> Dict:
        """
        Generate summary statistics from multiple analyses
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Summary statistics
        """
        if not analyses:
            return {
                'total_analyses': 0,
                'fake_count': 0,
                'real_count': 0,
                'average_confidence': 0.0
            }
        
        fake_count = sum(1 for a in analyses if a.get('classification', {}).get('status') == 'FAKE')
        real_count = sum(1 for a in analyses if a.get('classification', {}).get('status') == 'REAL')
        
        confidences = [a.get('classification', {}).get('confidence_score', 0) for a in analyses]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_analyses': len(analyses),
            'fake_count': fake_count,
            'real_count': real_count,
            'fake_percentage': f"{(fake_count / len(analyses) * 100):.1f}%",
            'real_percentage': f"{(real_count / len(analyses) * 100):.1f}%",
            'average_confidence': avg_confidence,
            'average_confidence_percentage': f"{avg_confidence * 100:.1f}%"
        }
    
    @staticmethod
    def format_for_api_response(dashboard_result: Dict) -> Dict:
        """
        Format dashboard result for API response
        
        Args:
            dashboard_result: Full dashboard result
            
        Returns:
            API-friendly formatted response
        """
        return {
            'success': True,
            'timestamp': dashboard_result['timestamp'],
            'result': {
                'prediction': dashboard_result['classification']['status'],
                'confidence': dashboard_result['classification']['confidence_percentage'],
                'verdict': dashboard_result['final_verdict'].get('verdict', 'UNKNOWN'),
            },
            'details': {
                'article': dashboard_result['article_info'],
                'analysis': dashboard_result['analysis_details'],
                'verification': {
                    'source_credibility': dashboard_result['source_verification'].get('credibility_score', 0.5),
                    'fact_check_status': dashboard_result['fact_check'].get('overall_verdict', 'not_checked'),
                },
                'recommendations': dashboard_result['recommendations'],
            },
            'visual': dashboard_result['visual_indicators']
        }
