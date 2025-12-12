"""
Test script for ReStockr authentication flow.

This script demonstrates the complete authentication workflow:
1. Signup
2. Get activation token from database
3. Activate account
4. Login
5. Access protected endpoints
6. Refresh token
7. Logout
"""

import asyncio
import httpx
from sqlalchemy import select
from app.database import get_db
from app.models.user import User


async def test_auth_flow():
    """Test complete authentication flow."""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("ReStockr Authentication Flow Test")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Step 1: Signup
        print("\n1. Creating new user signup...")
        signup_data = {
            "full_name": "Test User Auth",
            "email": "authtest@example.com",
            "phone_number": "8099999999",
            "role": "customer",
            "city": "Lagos",
            "password": "TestPass123",
        }

        response = await client.post(f"{base_url}/api/v1/user/signup", json=signup_data)
        if response.status_code == 201:
            print(f"   ✅ Signup successful: {response.json()['email']}")
        else:
            print(f"   ❌ Signup failed: {response.text}")
            return

        # Step 2: Get activation token from database
        print("\n2. Fetching activation token from database...")
        async for db in get_db():
            result = await db.execute(
                select(User).where(User.email == signup_data["email"])
            )
            user = result.scalar_one_or_none()
            if user and user.activation_token:
                activation_token = user.activation_token
                print(f"   ✅ Activation token: {activation_token[:20]}...")
            else:
                print("   ❌ Failed to get activation token")
                return
            break

        # Step 3: Activate account
        print("\n3. Activating account...")
        activation_data = {
            "email": signup_data["email"],
            "activation_token": activation_token,
        }

        response = await client.post(
            f"{base_url}/api/v1/auth/activate", json=activation_data
        )
        if response.status_code == 200:
            print(f"   ✅ Account activated: {response.json()['message']}")
        else:
            print(f"   ❌ Activation failed: {response.text}")
            return

        # Step 4: Login
        print("\n4. Logging in...")
        login_data = {
            "username": signup_data["email"],
            "password": signup_data["password"],
        }

        response = await client.post(f"{base_url}/api/v1/user/login", data=login_data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
            print(f"   ✅ Login successful")
            print(f"   📝 Access token: {access_token[:30]}...")
            print(f"   📝 Refresh token: {refresh_token[:30]}...")
            print(f"   ⏱️  Expires in: {tokens['expires_in']} seconds")
        else:
            print(f"   ❌ Login failed: {response.text}")
            return

        # Step 5: Access protected endpoint
        print("\n5. Accessing protected endpoint (GET /user/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(f"{base_url}/api/v1/user/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ Profile retrieved successfully")
            print(f"   👤 Name: {user_data['full_name']}")
            print(f"   📧 Email: {user_data['email']}")
            print(f"   📱 Phone: {user_data['phone_number']}")
            print(f"   👔 Role: {user_data['role']}")
            print(f"   🏙️  City: {user_data['city']}")
            print(f"   ✅ Active: {user_data['is_active']}")
        else:
            print(f"   ❌ Failed to get profile: {response.text}")
            return

        # Step 6: Update profile
        print("\n6. Updating user profile...")
        update_data = {"full_name": "Updated Test User", "city": "Abuja"}

        response = await client.patch(
            f"{base_url}/api/v1/user/me", json=update_data, headers=headers
        )
        if response.status_code == 200:
            updated = response.json()
            print(f"   ✅ Profile updated")
            print(f"   👤 New name: {updated['full_name']}")
            print(f"   🏙️  New city: {updated['city']}")
        else:
            print(f"   ❌ Update failed: {response.text}")

        # Step 7: Refresh token
        print("\n7. Refreshing access token...")
        refresh_data = {"refresh_token": refresh_token}

        response = await client.post(
            f"{base_url}/api/v1/auth/refresh", json=refresh_data
        )
        if response.status_code == 200:
            new_tokens = response.json()
            new_access_token = new_tokens["access_token"]
            print(f"   ✅ Token refreshed successfully")
            print(f"   📝 New access token: {new_access_token[:30]}...")
            # Update token for next request
            access_token = new_access_token
            refresh_token = new_tokens["refresh_token"]
        else:
            print(f"   ❌ Refresh failed: {response.text}")
            return

        # Step 8: Test with new token
        print("\n8. Testing new access token...")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(f"{base_url}/api/v1/user/me", headers=headers)
        if response.status_code == 200:
            print(f"   ✅ New token works correctly")
        else:
            print(f"   ❌ New token failed: {response.text}")

        # Step 9: Logout
        print("\n9. Logging out...")
        response = await client.post(f"{base_url}/api/v1/auth/logout", headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Logout successful: {response.json()['message']}")
        else:
            print(f"   ❌ Logout failed: {response.text}")

        # Step 10: Try using refresh token after logout (should fail)
        print("\n10. Testing refresh token after logout (should fail)...")
        refresh_data = {"refresh_token": refresh_token}

        response = await client.post(
            f"{base_url}/api/v1/auth/refresh", json=refresh_data
        )
        if response.status_code == 401:
            print(f"   ✅ Refresh correctly denied after logout")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nMake sure the server is running on http://localhost:8000")
    print("Starting test in 3 seconds...\n")

    import time

    time.sleep(3)

    asyncio.run(test_auth_flow())
