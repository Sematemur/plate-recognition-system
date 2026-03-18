def test_create_vehicle(client, db):
    response = client.post("/api/vehicles", json={
        "plate_number": "34ABC123",
        "plate_display": "34 ABC 123",
        "fuel_type": "dizel",
        "brand": "Toyota",
        "model": "Corolla",
        "color": "Beyaz",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["plate_number"] == "34ABC123"
    assert data["fuel_type"] == "dizel"


def test_create_vehicle_invalid_fuel_type(client, db):
    response = client.post("/api/vehicles", json={
        "plate_number": "34ABC123",
        "plate_display": "34 ABC 123",
        "fuel_type": "elektrik",
    })
    assert response.status_code == 422


def test_create_vehicle_duplicate_plate(client, db):
    payload = {
        "plate_number": "34ABC123",
        "plate_display": "34 ABC 123",
        "fuel_type": "dizel",
    }
    client.post("/api/vehicles", json=payload)
    response = client.post("/api/vehicles", json=payload)
    assert response.status_code == 409


def test_list_vehicles(client, db):
    client.post("/api/vehicles", json={
        "plate_number": "34ABC123",
        "plate_display": "34 ABC 123",
        "fuel_type": "dizel",
    })
    response = client.get("/api/vehicles")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["plate_number"] == "34ABC123"
