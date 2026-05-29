async def test_create_conversation(client):
    response = await client.post("/api/v1/conversations", json={})
    assert response.status_code == 201

async def test_get_all_conversations(client):
    response = await client.get("/api/v1/conversations")
    assert response.status_code == 200

async def test_get_conversatoin_by_id(client):
    create_response = await client.post("/api/v1/conversations", json={})
    conversation_id = create_response.json()["id"]
    response = await client.get(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 200

async def test_delete_conversation(client):
    create_response = await client.post("/api/v1/conversations", json={})
    conversation_id = create_response.json()["id"]
    response = await client.delete(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 404

async def test_update_conversation(client):
    create_response = await client.post("/api/v1/conversations", json={})
    conversation_id = create_response.json()["id"]
    response = await client.patch(f"/api/v1/conversations/{conversation_id}", json={
        "title": "new title"
    })
    assert response.status_code == 200