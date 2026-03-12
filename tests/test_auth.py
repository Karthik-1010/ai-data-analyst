import pytest
from app.models.user import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_register_user(client, db_session):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert "access_token" in data

    # Verify in DB
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "Test User"

@pytest.mark.asyncio
async def test_login_user(client, db_session):
    # First register
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User"
        },
    )

    # Then login
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me(client, db_session):
    # Register and login
    await client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "full_name": "Me User"
        },
    )
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "me@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    # Get /me
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"
