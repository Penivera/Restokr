"""
Analytics and metrics tracking for signups.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def get_signup_analytics(db: AsyncSession, days: int = 30) -> Dict:
    """
    Get comprehensive signup analytics.

    Args:
        db: Database session
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary with analytics data
    """
    logger.info(f"Generating signup analytics for last {days} days")

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total signups in period
    total_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= start_date)
    )
    total_signups = total_result.scalar_one()

    # Signups by role
    role_stats = {}
    for role in UserRole:
        role_result = await db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.role == role,
                    User.created_at >= start_date,
                )
            )
        )
        role_stats[role.value] = role_result.scalar_one()

    # Signups by city
    city_result = await db.execute(
        select(User.city, func.count(User.id).label("count"))
        .where(User.created_at >= start_date)
        .group_by(User.city)
        .order_by(func.count(User.id).desc())
    )
    city_stats = {city: count for city, count in city_result.all()}

    # Daily signup trend
    daily_result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    daily_trend = [
        {"date": str(date), "count": count} for date, count in daily_result.all()
    ]

    # Email confirmation rate
    confirmed_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.email_confirmed == True,
                User.created_at >= start_date,
            )
        )
    )
    confirmed_count = confirmed_result.scalar_one()
    confirmation_rate = (
        (confirmed_count / total_signups * 100) if total_signups > 0 else 0
    )

    # Growth rate (compare with previous period)
    previous_start = start_date - timedelta(days=days)
    previous_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.created_at >= previous_start,
                User.created_at < start_date,
            )
        )
    )
    previous_signups = previous_result.scalar_one()
    growth_rate = (
        ((total_signups - previous_signups) / previous_signups * 100)
        if previous_signups > 0
        else 100.0
    )

    logger.info(f"Analytics generated: {total_signups} signups in last {days} days")

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
        },
        "total_signups": total_signups,
        "growth_rate": round(growth_rate, 2),
        "by_role": role_stats,
        "by_city": city_stats,
        "daily_trend": daily_trend,
        "email_confirmation": {
            "confirmed": confirmed_count,
            "total": total_signups,
            "rate": round(confirmation_rate, 2),
        },
    }


async def get_recent_signups(db: AsyncSession, limit: int = 10) -> List[User]:
    """
    Get most recent signups.

    Args:
        db: Database session
        limit: Number of signups to retrieve

    Returns:
        List of recent signup records
    """
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
