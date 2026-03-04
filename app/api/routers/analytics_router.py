"""
Analytics Router for the Credit Score API.
Handles analytics endpoints including metrics, score distribution, and activity tracking.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.credit_score_repository import CreditScoreRepository
from app.schemas.error import ErrorResponse

router = APIRouter()


@router.get(
    "/analytics",
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_analytics(
    period: str = Query(default="30d", description="Time period (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db)
):
    """
    Get analytics metrics for the specified time period.
    
    Args:
        period: Time period for analytics (7d, 30d, 90d, 1y)
        db: Database session (injected)
        
    Returns:
        dict: Analytics data including metrics and trends
    """
    user_repo = UserRepository(db)
    credit_repo = CreditScoreRepository(db)
    
    # Calculate date range based on period
    end_date = datetime.now()
    if period == "7d":
        start_date = end_date - timedelta(days=7)
    elif period == "30d":
        start_date = end_date - timedelta(days=30)
    elif period == "90d":
        start_date = end_date - timedelta(days=90)
    elif period == "1y":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get all users and credit scores
    all_users = user_repo.get_all()
    users_with_scores = [user for user in all_users if hasattr(user, 'credit_scores') and user.credit_scores]
    
    # Calculate metrics
    total_users = len(all_users)
    users_with_credit_scores = len(users_with_scores)
    
    # Calculate average score
    if users_with_scores:
        avg_score = sum(score.score for user in users_with_scores for score in user.credit_scores[-1:]) / users_with_credit_scores
    else:
        avg_score = 0
    
    # Calculate high risk users (score < 600)
    high_risk_users = len([
        user for user in users_with_scores 
        if hasattr(user, 'credit_scores') and user.credit_scores and user.credit_scores[-1].score < 600
    ])
    
    # Get new scores in period
    new_scores = credit_repo.get_scores_by_date_range(start_date, end_date)
    
    # Calculate trends (simplified - in production would compare with previous period)
    users_trend = "+12.5"  # Placeholder
    score_trend = "+5.2"   # Placeholder
    risk_trend = "-2.1"   # Placeholder
    scores_trend = "+8.7" # Placeholder
    
    return {
        "metrics": {
            "total_users": total_users,
            "avg_score": round(avg_score, 1),
            "high_risk_users": high_risk_users,
            "new_scores": len(new_scores),
            "users_trend": users_trend,
            "score_trend": score_trend,
            "risk_trend": risk_trend,
            "scores_trend": scores_trend,
            "performance": {
                "calculations": len(new_scores),
                "registrations": total_users,  # Simplified
                "avg_score": round(avg_score, 1),
                "alerts": high_risk_users
            }
        },
        "period": period,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }


@router.get(
    "/analytics/score-distribution",
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_score_distribution(db: Session = Depends(get_db)):
    """
    Get credit score distribution across different ranges.
    
    Args:
        db: Database session (injected)
        
    Returns:
        dict: Score distribution data
    """
    user_repo = UserRepository(db)
    all_users = user_repo.get_all()
    users_with_scores = [user for user in all_users if hasattr(user, 'credit_scores') and user.credit_scores]
    
    # Initialize distribution
    distribution = {
        "excellent": 0,  # 750+
        "good": 0,       # 700-749
        "fair": 0,       # 650-699
        "poor": 0,       # 600-649
        "very_poor": 0   # <600
    }
    
    # Calculate distribution
    for user in users_with_scores:
        if hasattr(user, 'credit_scores') and user.credit_scores:
            latest_score = user.credit_scores[-1].score
            if latest_score >= 750:
                distribution["excellent"] += 1
            elif latest_score >= 700:
                distribution["good"] += 1
            elif latest_score >= 650:
                distribution["fair"] += 1
            elif latest_score >= 600:
                distribution["poor"] += 1
            else:
                distribution["very_poor"] += 1
    
    # Calculate risk categories
    total_users = len(users_with_scores)
    low_risk = distribution["excellent"] + distribution["good"]
    medium_risk = distribution["fair"]
    high_risk = distribution["poor"] + distribution["very_poor"]
    
    return {
        **distribution,
        "low_risk": low_risk,
        "medium_risk": medium_risk,
        "high_risk": high_risk,
        "total_users_with_scores": total_users
    }


@router.get(
    "/analytics/top-performers",
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_top_performers(
    limit: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get top performing users by credit score.
    
    Args:
        limit: Number of top performers to return
        db: Database session (injected)
        
    Returns:
        dict: Top performers data
    """
    user_repo = UserRepository(db)
    all_users = user_repo.get_all()
    users_with_scores = []
    
    # Get users with their latest credit scores
    for user in all_users:
        if hasattr(user, 'credit_scores') and user.credit_scores:
            users_with_scores.append({
                "id": user.id,
                "fullname": user.fullname,
                "creditScore": {
                    "score": user.credit_scores[-1].score
                }
            })
    
    # Sort by score (descending) and take top performers
    top_performers = sorted(
        users_with_scores, 
        key=lambda x: x["creditScore"]["score"], 
        reverse=True
    )[:limit]
    
    return {
        "performers": top_performers,
        "limit": limit
    }


@router.get(
    "/analytics/recent-activity",
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent activity in the system.
    
    Args:
        limit: Number of recent activities to return
        db: Database session (injected)
        
    Returns:
        dict: Recent activity data
    """
    credit_repo = CreditScoreRepository(db)
    user_repo = UserRepository(db)
    
    # Get recent credit score calculations
    recent_scores = credit_repo.get_recent_scores(limit)
    
    activities = []
    for score in recent_scores:
        user = user_repo.get_by_id(score.user_id)
        if user:
            activities.append({
                "id": f"score_{score.id}",
                "type": "score_calculated",
                "title": f"Credit score calculated for {user.fullname}",
                "time": _format_time_ago(score.calculated_at),
                "user_id": user.id,
                "score": score.score
            })
    
    # If no activities, create some sample ones based on recent users
    if not activities:
        recent_users = user_repo.get_all()[:5]
        for i, user in enumerate(recent_users):
            activities.append({
                "id": f"user_{user.id}",
                "type": "user_registered" if i % 2 == 0 else "score_calculated",
                "title": f"{'New user registered' if i % 2 == 0 else 'Credit score calculated'} for {user.fullname}",
                "time": f"{(i + 1) * 5} minutes ago",
                "user_id": user.id
            })
    
    return {
        "activities": activities[:limit],
        "limit": limit
    }


def _format_time_ago(created_at: datetime) -> str:
    """
    Format a datetime as a relative time string.
    
    Args:
        created_at: The datetime to format
        
    Returns:
        str: Relative time string (e.g., "2 minutes ago")
    """
    now = datetime.now()
    diff = now - created_at
    
    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(diff.days / 7)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
