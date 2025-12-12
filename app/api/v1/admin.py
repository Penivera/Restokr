import csv
import json
import logging
from io import StringIO, BytesIO
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from openpyxl import Workbook
from app.api.deps import DBSessionDep, AdminDep
from app.models.user import User, UserRole
from app.schemas.user import UserListResponse, UserResponse
from app.config import settings
from app.core.analytics import get_signup_analytics, get_recent_signups

router = APIRouter(prefix="/api/v1/admin")
logger = logging.getLogger(__name__)


@router.get(
    "/signups",
    response_model=UserListResponse,
    summary="List All Users (Admin)",
    description="Get paginated list of all users. Requires admin authentication.",
)
async def list_users(
    db: DBSessionDep,
    admin: AdminDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page",
    ),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    city: str | None = Query(default=None, description="Filter by city"),
) -> UserListResponse:
    """
    List all users with pagination and filtering.

    Requires HTTP Basic Auth with admin credentials.
    """
    # Build base query
    query = select(User)

    # Apply filters
    if role:
        query = query.where(User.role == role)
    if city:
        query = query.where(User.city == city)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=[UserResponse.model_validate(u) for u in users],
    )


@router.get(
    "/export",
    summary="Export Users (Admin)",
    description="Export all users in CSV, JSON, or Excel format. Requires admin authentication.",
)
async def export_users(
    db: DBSessionDep,
    admin: AdminDep,
    format: str = Query(
        default="csv", regex="^(csv|json|excel)$", description="Export format"
    ),
    role: UserRole | None = Query(default=None, description="Filter by role"),
) -> StreamingResponse:
    """
    Export all users in specified format.

    - **format**: csv, json, or excel
    - **role**: Optional filter by user role

    Requires HTTP Basic Auth with admin credentials.
    """
    # Build query
    query = select(User).order_by(User.created_at.desc())

    if role:
        query = query.where(User.role == role)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No users found to export"
        )

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    role_suffix = f"_{role.value}" if role else "_all"

    # Export based on format
    if format == "csv":
        return _export_csv(users, f"restokr_users{role_suffix}_{timestamp}.csv")
    elif format == "json":
        return _export_json(users, f"restokr_users{role_suffix}_{timestamp}.json")
    elif format == "excel":
        return _export_excel(users, f"restokr_users{role_suffix}_{timestamp}.xlsx")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Use: csv, json, or excel",
        )


def _export_csv(users: list[User], filename: str) -> StreamingResponse:
    """Export users as CSV."""
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "ID",
            "Full Name",
            "Email",
            "Phone Number",
            "Role",
            "City",
            "Created At",
            "Email Confirmed",
            "Exported",
        ]
    )

    # Write data
    for user in users:
        writer.writerow(
            [
                user.id,
                user.full_name,
                user.email,
                user.phone_number,
                user.role.value,
                user.city,
                user.created_at.isoformat(),
                user.email_confirmed,
                user.is_exported,
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_json(users: list[User], filename: str) -> StreamingResponse:
    """Export users as JSON."""
    data = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone_number": u.phone_number,
            "role": u.role.value,
            "city": u.city,
            "created_at": u.created_at.isoformat(),
            "email_confirmed": u.email_confirmed,
            "is_exported": u.is_exported,
        }
        for u in users
    ]

    json_str = json.dumps(data, indent=2)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_excel(users: list[User], filename: str) -> StreamingResponse:
    """Export users as Excel."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Users"

    # Write header
    headers = [
        "ID",
        "Full Name",
        "Email",
        "Phone Number",
        "Role",
        "City",
        "Created At",
        "Email Confirmed",
        "Exported",
    ]
    ws.append(headers)

    # Style header
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

    # Write data
    for user in users:
        ws.append(
            [
                user.id,
                user.full_name,
                user.email,
                user.phone_number,
                user.role.value,
                user.city,
                user.created_at.isoformat(),
                user.email_confirmed,
                user.is_exported,
            ]
        )

    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to bytes
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/stats",
    summary="Get User Statistics (Admin)",
    description="Get statistics about users. Requires admin authentication.",
)
async def get_stats(
    db: DBSessionDep,
    admin: AdminDep,
) -> dict:
    """
    Get user statistics.

    Requires HTTP Basic Auth with admin credentials.
    """
    # Total users
    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar_one()

    # Count by role
    role_counts = {}
    for role in UserRole:
        role_result = await db.execute(
            select(func.count(User.id)).where(User.role == role)
        )
        role_counts[role.value] = role_result.scalar_one()

    # Count by city
    city_result = await db.execute(
        select(User.city, func.count(User.id)).group_by(User.city)
    )
    city_counts = {city: count for city, count in city_result.all()}

    # Email confirmation rate
    confirmed_result = await db.execute(
        select(func.count(User.id)).where(User.email_confirmed == True)
    )
    confirmed = confirmed_result.scalar_one()

    return {
        "total_users": total,
        "by_role": role_counts,
        "by_city": city_counts,
        "email_confirmed": confirmed,
        "confirmation_rate": f"{(confirmed/total*100):.1f}%" if total > 0 else "0%",
    }


@router.get(
    "/analytics",
    summary="Get Advanced Analytics (Admin)",
    description="Get comprehensive analytics including trends and growth metrics. Requires admin authentication.",
)
async def get_analytics(
    db: DBSessionDep,
    admin: AdminDep,
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
) -> dict:
    """
    Get advanced analytics with trends and growth metrics.

    Requires HTTP Basic Auth with admin credentials.
    """
    logger.info(f"Admin requesting analytics for last {days} days")
    analytics = await get_signup_analytics(db, days=days)
    logger.info("Analytics data retrieved successfully")
    return analytics


@router.get(
    "/recent",
    summary="Get Recent Users (Admin)",
    description="Get the most recent users. Requires admin authentication.",
)
async def get_recent(
    db: DBSessionDep,
    admin: AdminDep,
    limit: int = Query(default=10, ge=1, le=100, description="Number of recent users"),
) -> dict:
    """
    Get recent users.

    Requires HTTP Basic Auth with admin credentials.
    """
    logger.info(f"Admin requesting {limit} recent users")
    recent = await get_recent_signups(db, limit=limit)
    return {
        "count": len(recent),
        "users": [UserResponse.model_validate(s) for s in recent],
    }
