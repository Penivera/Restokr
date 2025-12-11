from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.api.deps import DBSessionDep
from app.models.signup import EarlyAccessSignup
from app.schemas.signup import EarlyAccessSignupCreate, EarlyAccessSignupResponse
from app.core.email import send_confirmation_email

router = APIRouter(prefix="/api/v1/signup")


@router.post(
    "",
    response_model=EarlyAccessSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Early Access Signup",
    description="Register for early access to ReStockr platform",
)
async def create_signup(
    signup_data: EarlyAccessSignupCreate,
    db: DBSessionDep,
    background_tasks: BackgroundTasks,
) -> EarlyAccessSignup:
    """
    Create a new early access signup.

    - **full_name**: User's full name
    - **email**: Valid email address (must be unique)
    - **phone_number**: Phone number (auto-prepends +234 for Nigerian numbers)
    - **role**: User role - customer, vendor, or rider
    - **city**: City location (defaults to Abuja)
    """
    # Check if email already exists
    existing_email = await db.execute(
        select(EarlyAccessSignup).where(EarlyAccessSignup.email == signup_data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered for early access",
        )

    # Check if phone number already exists
    existing_phone = await db.execute(
        select(EarlyAccessSignup).where(
            EarlyAccessSignup.phone_number == str(signup_data.phone_number)
        )
    )
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already registered for early access",
        )

    # Create new signup
    try:
        new_signup = EarlyAccessSignup(
            full_name=signup_data.full_name,
            email=signup_data.email,
            phone_number=str(signup_data.phone_number),
            role=signup_data.role,
            city=signup_data.city,
        )

        db.add(new_signup)
        await db.flush()  # Flush to get the ID
        await db.refresh(new_signup)

        # Send confirmation email in background
        background_tasks.add_task(
            send_confirmation_email,
            to_email=new_signup.email,
            full_name=new_signup.full_name,
            role=new_signup.role.value,
        )

        return new_signup

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or phone number already exists",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your signup: {str(e)}",
        )
