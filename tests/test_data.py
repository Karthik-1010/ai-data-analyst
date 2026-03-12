import pytest
from datetime import date

@pytest.fixture
async def auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "data@example.com", "password": "password123", "full_name": "Data User"}
    )
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "data@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_data_record(client, auth_header):
    response = await client.post(
        "/api/data/",
        headers=auth_header,
        json={
            "employee_name": "John Doe",
            "department": "Engineering",
            "salary": 75000,
            "performance_score": 85.5,
            "record_date": "2024-03-12"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employee_name"] == "John Doe"
    assert data["salary"] == 75000

@pytest.mark.asyncio
async def test_list_data_records(client, auth_header):
    # Create one record first
    await client.post(
        "/api/data/",
        headers=auth_header,
        json={
            "employee_name": "Jane Smith",
            "department": "HR",
            "salary": 65000,
            "performance_score": 90.0,
            "record_date": "2024-03-12"
        },
    )

    response = await client.get("/api/data/", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert len(data["records"]) >= 1
    assert data["records"][0]["employee_name"] in ["Jane Smith", "John Doe"]
