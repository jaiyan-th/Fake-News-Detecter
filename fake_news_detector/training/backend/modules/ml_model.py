"""
Module 4: Machine Learning Model
Supports multiple ML algorithms: Logistic Regression, Random Forest, SVM, and more
"""

import pickle
import os
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeNewsClassifier:
    """Machine Learning classifier for fake news detection"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self.model_type = "Unknown"
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, path: str):
        """Load pre-trained model"""
        try:
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Detect model type
            model_class = self.model.__class__.__name__
            self.model_type = model_class
            
            logger.info(f"Model loaded: {model_class} from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict if news is fake or real
        
        Args:
            features: Feature vector (TF-IDF)
            
        Returns:
            Tuple of (prediction, confidence_score)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return "UNKNOWN", 0.0
        
        try:
            # Get prediction
            prediction = self.model.predict(features)[0]
            
            # Get confidence score
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)[0]
                confidence = float(max(probabilities))
            elif hasattr(self.model, 'decision_function'):
                decision = self.model.decision_function(features)[0]
                # Convert decision function to probability-like score
                confidence = float(1 / (1 + np.exp(-abs(decision))))
            else:
                confidence = 0.85  # Default confidence
            
            # Map prediction to label
            label = "REAL" if prediction == 1 else "FAKE"
            
            return label, confidence
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            return "ERROR", 0.0
    
    def predict_with_details(self, article: Dict) -> Dict:
        """
        Predict with detailed analysis
        
        Args:
            article: Article dictionary with 'tfidf_features'
            
        Returns:
            Prediction results with details
        """
        features = article.get('tfidf_features')
        
        if features is None or features.size == 0:
            return {
                'prediction': 'ERROR',
                'confidence': 0.0,
                'error': 'No features available'
            }
        
        prediction, confidence = self.predict(features)
        
        # Build detailed result
        result = {
            'prediction': prediction,
            'confidence': confidence,
            'confidence_percentage': f"{confidence * 100:.1f}%",
            'model_type': self.model_type,
            'feature_signals': article.get('feature_signals', []),
            'sentiment_analysis': article.get('sentiment_features', {}),
            'linguistic_features': article.get('linguistic_features', {}),
        }
        
        # Add interpretation
        result['interpretation'] = self._interpret_prediction(prediction, confidence, article)
        
        return result
    
    def _interpret_prediction(self, prediction: str, confidence: float, article: Dict) -> str:
        """Generate human-readable interpretation"""
        
        if prediction == "FAKE":
            if confidence > 0.9:
                return "High confidence: This article shows strong indicators of fake news."
            elif confidence > 0.7:
                return "Moderate confidence: This article has several suspicious characteristics."
            else:
                return "Low confidence: Some indicators suggest this might be fake news."
        else:
            if confidence > 0.9:
                return "High confidence: This article appears to be legitimate news."
            elif confidence > 0.7:
                return "Moderate confidence: This article seems credible but verify sources."
            else:
                return "Low confidence: Unable to determine with certainty."


class ModelEnsemble:
    """Ensemble of multiple models for improved accuracy"""
    
    def __init__(self, model_paths: Dict[str, str]):
        """
        Initialize ensemble with multiple models
        
        Args:
            model_paths: Dictionary mapping model names to file paths
        """
        self.models = {}
        
        for name, path in model_paths.items():
            if os.path.exists(path):
                classifier = FakeNewsClassifier(path)
                if classifier.model is not None:
                    self.models[name] = classifier
                    logger.info(f"Loaded model: {name}")
    
    def predict_ensemble(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict using ensemble voting
        
        Args:
            features: Feature vector
            
        Returns:
            Tuple of (prediction, confidence)
        """
        if not self.models:
            return "UNKNOWN", 0.0
        
        predictions = []
        confidences = []
        
        for name, classifier in self.models.items():
            pred, conf = classifier.predict(features)
            predictions.append(pred)
            confidences.append(conf)
        
        # Majority voting
        fake_count = predictions.count("FAKE")
        real_count = predictions.count("REAL")
        
        if fake_count > real_count:
            final_prediction = "FAKE"
        else:
            final_prediction = "REAL"
        
        # Average confidence
        final_confidence = np.mean(confidences)
        
        return final_prediction, final_confidence
