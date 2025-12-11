import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from openpyxl import Workbook
from app.api.deps import DBSessionDep, AdminDep
from app.models.signup import EarlyAccessSignup, UserRole
from app.schemas.signup import SignupListResponse, EarlyAccessSignupResponse
from app.config import settings

router = APIRouter(prefix="/api/v1/admin")


@router.get(
    "/signups",
    response_model=SignupListResponse,
    summary="List All Signups (Admin)",
    description="Get paginated list of all early access signups. Requires admin authentication."
)
async def list_signups(
    db: DBSessionDep,
    admin: AdminDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page"
    ),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    city: str | None = Query(default=None, description="Filter by city"),
) -> SignupListResponse:
    """
    List all early access signups with pagination and filtering.
    
    Requires HTTP Basic Auth with admin credentials.
    """
    # Build base query
    query = select(EarlyAccessSignup)
    
    # Apply filters
    if role:
        query = query.where(EarlyAccessSignup.role == role)
    if city:
        query = query.where(EarlyAccessSignup.city == city)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(EarlyAccessSignup.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    signups = result.scalars().all()
    
    return SignupListResponse(
        total=total,
        page=page,
        page_size=page_size,
        signups=[EarlyAccessSignupResponse.model_validate(s) for s in signups]
    )


@router.get(
    "/export",
    summary="Export Signups (Admin)",
    description="Export all signups in CSV, JSON, or Excel format. Requires admin authentication."
)
async def export_signups(
    db: DBSessionDep,
    admin: AdminDep,
    format: str = Query(default="csv", regex="^(csv|json|excel)$", description="Export format"),
    role: UserRole | None = Query(default=None, description="Filter by role"),
) -> StreamingResponse:
    """
    Export all signups in specified format.
    
    - **format**: csv, json, or excel
    - **role**: Optional filter by user role
    
    Requires HTTP Basic Auth with admin credentials.
    """
    # Build query
    query = select(EarlyAccessSignup).order_by(EarlyAccessSignup.created_at.desc())
    
    if role:
        query = query.where(EarlyAccessSignup.role == role)
    
    # Execute query
    result = await db.execute(query)
    signups = result.scalars().all()
    
    if not signups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No signups found to export"
        )
    
    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    role_suffix = f"_{role.value}" if role else "_all"
    
    # Export based on format
    if format == "csv":
        return _export_csv(signups, f"restokr_signups{role_suffix}_{timestamp}.csv")
    elif format == "json":
        return _export_json(signups, f"restokr_signups{role_suffix}_{timestamp}.json")
    elif format == "excel":
        return _export_excel(signups, f"restokr_signups{role_suffix}_{timestamp}.xlsx")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Use: csv, json, or excel"
        )


def _export_csv(signups: list[EarlyAccessSignup], filename: str) -> StreamingResponse:
    """Export signups as CSV."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Full Name", "Email", "Phone Number", "Role", "City", 
        "Created At", "Email Confirmed", "Exported"
    ])
    
    # Write data
    for signup in signups:
        writer.writerow([
            signup.id,
            signup.full_name,
            signup.email,
            signup.phone_number,
            signup.role.value,
            signup.city,
            signup.created_at.isoformat(),
            signup.email_confirmed,
            signup.is_exported
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_json(signups: list[EarlyAccessSignup], filename: str) -> StreamingResponse:
    """Export signups as JSON."""
    data = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "email": s.email,
            "phone_number": s.phone_number,
            "role": s.role.value,
            "city": s.city,
            "created_at": s.created_at.isoformat(),
            "email_confirmed": s.email_confirmed,
            "is_exported": s.is_exported
        }
        for s in signups
    ]
    
    json_str = json.dumps(data, indent=2)
    
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_excel(signups: list[EarlyAccessSignup], filename: str) -> StreamingResponse:
    """Export signups as Excel."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Early Access Signups"
    
    # Write header
    headers = [
        "ID", "Full Name", "Email", "Phone Number", "Role", "City",
        "Created At", "Email Confirmed", "Exported"
    ]
    ws.append(headers)
    
    # Style header
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    
    # Write data
    for signup in signups:
        ws.append([
            signup.id,
            signup.full_name,
            signup.email,
            signup.phone_number,
            signup.role.value,
            signup.city,
            signup.created_at.isoformat(),
            signup.email_confirmed,
            signup.is_exported
        ])
    
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
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/stats",
    summary="Get Signup Statistics (Admin)",
    description="Get statistics about early access signups. Requires admin authentication."
)
async def get_stats(
    db: DBSessionDep,
    admin: AdminDep,
) -> dict:
    """
    Get signup statistics.
    
    Requires HTTP Basic Auth with admin credentials.
    """
    # Total signups
    total_result = await db.execute(select(func.count(EarlyAccessSignup.id)))
    total = total_result.scalar_one()
    
    # Count by role
    role_counts = {}
    for role in UserRole:
        role_result = await db.execute(
            select(func.count(EarlyAccessSignup.id)).where(EarlyAccessSignup.role == role)
        )
        role_counts[role.value] = role_result.scalar_one()
    
    # Count by city
    city_result = await db.execute(
        select(EarlyAccessSignup.city, func.count(EarlyAccessSignup.id))
        .group_by(EarlyAccessSignup.city)
    )
    city_counts = {city: count for city, count in city_result.all()}
    
    # Email confirmation rate
    confirmed_result = await db.execute(
        select(func.count(EarlyAccessSignup.id)).where(EarlyAccessSignup.email_confirmed == True)
    )
    confirmed = confirmed_result.scalar_one()
    
    return {
        "total_signups": total,
        "by_role": role_counts,
        "by_city": city_counts,
        "email_confirmed": confirmed,
        "confirmation_rate": f"{(confirmed/total*100):.1f}%" if total > 0 else "0%"
    }
