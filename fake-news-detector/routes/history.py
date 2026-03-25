"""
Analysis history routes
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import db
from models.user_analysis import UserAnalysis
from datetime import datetime

history_bp = Blueprint('history', __name__, url_prefix='/api/history')

@history_bp.route('/', methods=['GET'])
@login_required
def get_history():
    """Get user's analysis history"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get filter parameters
        input_type = request.args.get('type', None)  # 'url' or 'text'
        verdict = request.args.get('verdict', None)  # 'REAL', 'FAKE', 'UNCERTAIN'
        
        # Build query
        query = UserAnalysis.query.filter_by(user_id=current_user.id)
        
        if input_type:
            query = query.filter_by(input_type=input_type)
        
        if verdict:
            query = query.filter_by(verdict=verdict)
        
        # Order by most recent first
        query = query.order_by(UserAnalysis.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert to dict
        analyses = [analysis.to_dict() for analysis in pagination.items]
        
        return jsonify({
            'analyses': analyses,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get user's analysis statistics"""
    try:
        # Total analyses
        total = UserAnalysis.query.filter_by(user_id=current_user.id).count()
        
        # Verdict distribution
        real_count = UserAnalysis.query.filter_by(user_id=current_user.id, verdict='REAL').count()
        fake_count = UserAnalysis.query.filter_by(user_id=current_user.id, verdict='FAKE').count()
        uncertain_count = UserAnalysis.query.filter_by(user_id=current_user.id, verdict='UNCERTAIN').count()
        
        # Average confidence
        analyses = UserAnalysis.query.filter_by(user_id=current_user.id).all()
        avg_confidence = sum(a.confidence for a in analyses) / len(analyses) if analyses else 0
        
        return jsonify({
            'total_analyses': total,
            'verdict_distribution': {
                'REAL': real_count,
                'FAKE': fake_count,
                'UNCERTAIN': uncertain_count
            },
            'average_confidence': round(avg_confidence * 100, 1)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/<int:analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id):
    """Get specific analysis by ID"""
    try:
        analysis = UserAnalysis.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        return jsonify(analysis.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis(analysis_id):
    """Delete specific analysis"""
    try:
        analysis = UserAnalysis.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        db.session.delete(analysis)
        db.session.commit()
        
        return jsonify({'message': 'Analysis deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@history_bp.route('/clear', methods=['DELETE'])
@login_required
def clear_history():
    """Clear all user's analysis history"""
    try:
        UserAnalysis.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        return jsonify({'message': 'History cleared successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def save_user_analysis(user_id: int, input_type: str, input_content: str,
                       verdict: str, confidence: float, explanation: str = None,
                       matched_articles_count: int = 0, processing_time: float = None):
    """
    Helper function to save user analysis
    Called from analyze routes after analysis is complete
    """
    try:
        analysis = UserAnalysis(
            user_id=user_id,
            input_type=input_type,
            input_content=input_content,
            verdict=verdict,
            confidence=confidence,
            explanation=explanation,
            matched_articles_count=matched_articles_count,
            processing_time=processing_time
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return analysis.id
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to save user analysis: {str(e)}")
        return None
