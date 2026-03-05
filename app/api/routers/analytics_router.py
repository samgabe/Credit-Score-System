"""
Analytics Router for the Credit Score API.
Handles analytics endpoints including metrics, score distribution, and activity tracking.
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.credit_score_repository import CreditScoreRepository
from app.repositories.credit_subject_repository import CreditSubjectRepository
from app.schemas.error import ErrorResponse
from app.api.routers.system_auth_router import get_current_system_user, require_role
from app.models.system_user import SystemUser

router = APIRouter()


@router.get(
    "/analytics",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_analytics(
    period: str = Query(default="30d", description="Time period (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
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
    
    # Get all credit subjects with their scores
    credit_subject_repo = CreditSubjectRepository(db)
    all_subjects = credit_subject_repo.get_all(limit=1000, offset=0)
    subjects_with_scores = []
    
    for subject in all_subjects:
        # Get scores for this subject
        subject_scores = credit_repo.get_by_credit_subject_id(str(subject.id))
        if subject_scores:
            # Add scores to subject object
            subject.credit_scores = subject_scores
            subjects_with_scores.append(subject)
    
    # Calculate metrics
    total_subjects = len(all_subjects)
    subjects_with_credit_scores_count = len(subjects_with_scores)
    
    # Calculate average score
    if subjects_with_credit_scores_count:
        avg_score = sum(score.score for subject in subjects_with_scores for score in subject.credit_scores[-1:]) / subjects_with_credit_scores_count
    else:
        avg_score = 0
    
    # Calculate high risk subjects (score < 600)
    high_risk_subjects = sum(1 for subject in subjects_with_scores 
        if hasattr(subject, 'credit_scores') and subject.credit_scores and subject.credit_scores[-1].score < 600
    )
    
    # Get new scores in period
    new_scores = credit_repo.get_scores_by_date_range(start_date, end_date)
    
    # Calculate trends (simplified - in production would compare with previous period)
    subjects_trend = "+12.5"  # Placeholder
    score_trend = "+5.2"   # Placeholder
    risk_trend = "-2.1"   # Placeholder
    scores_trend = "+8.7" # Placeholder
    
    return {
        "metrics": {
            "total_subjects": total_subjects,
            "total_users": total_subjects,  # Keep for backward compatibility
            "avg_score": round(avg_score, 1),
            "high_risk_subjects": high_risk_subjects,
            "high_risk_users": high_risk_subjects,  # Keep for backward compatibility
            "new_scores": len(new_scores),
            "subjects_trend": subjects_trend,
            "users_trend": subjects_trend,  # Keep for backward compatibility
            "score_trend": score_trend,
            "risk_trend": risk_trend,
            "scores_trend": scores_trend,
            "performance": {
                "calculations": len(new_scores),
                "registrations": total_subjects,  # Simplified
                "avg_score": round(avg_score, 1),
                "alerts": high_risk_subjects
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_score_distribution(
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
):
    """
    Get credit score distribution across different ranges.
    
    Args:
        db: Database session (injected)
        current_user: Current authenticated system user
        
    Returns:
        dict: Score distribution data
    """
    credit_subject_repo = CreditSubjectRepository(db)
    credit_score_repo = CreditScoreRepository(db)
    
    # Get all credit subjects with their scores
    all_subjects = credit_subject_repo.get_all(limit=1000, offset=0)
    subjects_with_scores = []
    
    for subject in all_subjects:
        # Get scores for this subject
        subject_scores = credit_score_repo.get_by_credit_subject_id(str(subject.id))
        if subject_scores:
            # Add scores to subject object
            subject.credit_scores = subject_scores
            subjects_with_scores.append(subject)
    
    # Initialize distribution
    distribution = {
        "excellent": 0,  # 750+
        "good": 0,       # 700-749
        "fair": 0,       # 650-699
        "poor": 0,       # 600-649
        "very_poor": 0   # <600
    }
    
    # Calculate distribution
    for subject in subjects_with_scores:
        if hasattr(subject, 'credit_scores') and subject.credit_scores:
            latest_score = subject.credit_scores[-1].score
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
    total_subjects = len(subjects_with_scores)
    low_risk = distribution["excellent"] + distribution["good"]
    medium_risk = distribution["fair"]
    high_risk = distribution["poor"] + distribution["very_poor"]
    
    return {
        **distribution,
        "low_risk": low_risk,
        "medium_risk": medium_risk,
        "high_risk": high_risk,
        "total_subjects_with_scores": total_subjects,
        "total_users_with_scores": total_subjects  # Keep for backward compatibility
    }


@router.get(
    "/analytics/top-performers",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_top_performers(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(require_role("viewer"))
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


@router.get(
    "/analytics/score-trends",
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["analytics"]
)
def get_score_trends(
    period: str = Query(default="30d", description="Time period (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db)
):
    """
    Get credit score trends over time.
    
    Args:
        period: Time period for trends (7d, 30d, 90d, 1y)
        db: Database session (injected)
        
    Returns:
        dict: Score trends data with historical points
    """
    credit_repo = CreditScoreRepository(db)
    user_repo = UserRepository(db)
    
    # Calculate date range based on period
    end_date = datetime.now()
    if period == "7d":
        start_date = end_date - timedelta(days=7)
        months = []
        avg_scores = []
        new_users = []
        
        # Generate daily data for 7 days
        for i in range(7):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # Get scores for this day
            day_scores = credit_repo.get_scores_by_date_range(day_start, day_end)
            users_with_scores = user_repo.get_all()
            
            # Calculate average score for this day
            if day_scores:
                avg_score = sum(score.score for score in day_scores) / len(day_scores)
            else:
                # Use previous day's average or 0
                avg_score = avg_scores[-1] if avg_scores else 0
            
            # Get new users for this day
            new_users_count = len([
                user for user in users_with_scores 
                if user.created_at >= day_start and user.created_at < day_end
            ])
            
            months.append(day_start.strftime("%b %d"))
            avg_scores.append(round(avg_score, 1))
            new_users.append(new_users_count)
            
    elif period == "30d":
        start_date = end_date - timedelta(days=30)
        months = []
        avg_scores = []
        new_users = []
        
        # Generate weekly data for 30 days (4 weeks + 2 days)
        for i in range(0, 30, 7):
            week_start = start_date + timedelta(days=i)
            week_end = min(week_start + timedelta(days=7), end_date)
            
            # Get scores for this week
            week_scores = credit_repo.get_scores_by_date_range(week_start, week_end)
            
            # Calculate average score for this week
            if week_scores:
                avg_score = sum(score.score for score in week_scores) / len(week_scores)
            else:
                avg_score = avg_scores[-1] if avg_scores else 0
            
            # Get new users for this week
            users_with_scores = user_repo.get_all()
            new_users_count = len([
                user for user in users_with_scores 
                if user.created_at >= week_start and user.created_at < week_end
            ])
            
            months.append(f"Week {i//7 + 1}")
            avg_scores.append(round(avg_score, 1))
            new_users.append(new_users_count)
            
    elif period == "90d":
        start_date = end_date - timedelta(days=90)
        months = []
        avg_scores = []
        new_users = []
        
        # Generate monthly data for 90 days (3 months)
        for i in range(3):
            month_start = start_date + timedelta(days=i * 30)
            month_end = min(month_start + timedelta(days=30), end_date)
            
            # Get scores for this month
            month_scores = credit_repo.get_scores_by_date_range(month_start, month_end)
            
            # Calculate average score for this month
            if month_scores:
                avg_score = sum(score.score for score in month_scores) / len(month_scores)
            else:
                avg_score = avg_scores[-1] if avg_scores else 0
            
            # Get new users for this month
            users_with_scores = user_repo.get_all()
            new_users_count = len([
                user for user in users_with_scores 
                if user.created_at >= month_start and user.created_at < month_end
            ])
            
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            months.append(month_names[month_start.month - 1])
            avg_scores.append(round(avg_score, 1))
            new_users.append(new_users_count)
            
    else:  # 1y
        start_date = end_date - timedelta(days=365)
        months = []
        avg_scores = []
        new_users = []
        
        # Generate monthly data for 1 year
        current_date = start_date
        while current_date < end_date:
            month_end = min(current_date + timedelta(days=30), end_date)
            
            # Get scores for this month
            month_scores = credit_repo.get_scores_by_date_range(current_date, month_end)
            
            # Calculate average score for this month
            if month_scores:
                avg_score = sum(score.score for score in month_scores) / len(month_scores)
            else:
                avg_score = avg_scores[-1] if avg_scores else 0
            
            # Get new users for this month
            users_with_scores = user_repo.get_all()
            new_users_count = len([
                user for user in users_with_scores 
                if user.created_at >= current_date and user.created_at < month_end
            ])
            
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            months.append(month_names[current_date.month - 1])
            avg_scores.append(round(avg_score, 1))
            new_users.append(new_users_count)
            
            current_date = month_end
    
    try:
        return {
            "period": period,
            "labels": months,
            "avgScores": avg_scores,
            "newUsers": new_users,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve score trends: {str(e)}"
        )


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
