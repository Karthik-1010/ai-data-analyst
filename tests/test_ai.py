import pytest
from unittest.mock import patch

@pytest.fixture
async def auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "ai@example.com", "password": "password123", "full_name": "AI User"}
    )
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "ai@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_chat_api(client, auth_header):
    with patch("app.routers.ai.chat_with_agent") as mock_chat:
        mock_chat.return_value = "This is a mocked answer."
        
        response = await client.post(
            "/api/ai/chat",
            headers=auth_header,
            json={"question": "What is the total salary?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a mocked answer."
        assert data["question"] == "What is the total salary?"

@pytest.mark.asyncio
async def test_get_chat_history(client, auth_header):
    # Add a message to history
    with patch("app.routers.ai.chat_with_agent") as mock_chat:
        mock_chat.return_value = "History answer."
        await client.post(
            "/api/ai/chat",
            headers=auth_header,
            json={"question": "History question?"}
        )

    response = await client.get("/api/ai/history", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert len(data["conversations"]) >= 1
    assert data["conversations"][0]["question"] == "History question?"
