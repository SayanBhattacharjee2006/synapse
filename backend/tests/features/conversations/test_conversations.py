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

async def test_create_message(client):
    created_convo = await client.post("/api/v1/conversations", json={})
    conversation_id = created_convo.json()["id"]

    response = await client.post(f"/api/v1/conversations/{conversation_id}/messages", json={
        "content": "hello world",
        "sender": "user"
    })
    assert response.status_code == 201

async def test_get_messages(client):
    created_convo = await client.post("/api/v1/conversations", json={})
    conversation_id = created_convo.json()["id"]

    await client.post(f"/api/v1/conversations/{conversation_id}/messages", json={
        "content": "hello world",
        "sender": "user"
    })

    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert response.status_code == 200

async def test_delete_message(client):
    created_convo = await client.post("/api/v1/conversations", json={})
    conversation_id = created_convo.json()["id"]

    created_msg = await client.post(f"/api/v1/conversations/{conversation_id}/messages", json={
        "content": "hello world",
        "sender": "user"
    })
    message_id = created_msg.json()["id"]

    response = await client.delete(f"/api/v1/conversations/{conversation_id}/messages/{message_id}")
    assert response.status_code == 204

    response = await client.delete(f"/api/v1/conversations/{conversation_id}/messages/{message_id}")
    assert response.status_code == 404

async def test_get_messages_empty(client):
    created_convo = await client.post("/api/v1/conversations", json={})
    conversation_id = created_convo.json()["id"]

    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert response.status_code == 200