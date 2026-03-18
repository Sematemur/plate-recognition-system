from app.models import RecognitionLog, Vehicle


def test_list_logs(client, db):
    log = RecognitionLog(
        plate_detected="34 ABC 123",
        is_known=False,
        confidence=0.9,
        det_confidence=0.95,
    )
    db.add(log)
    db.commit()

    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_confirm_log(client, db):
    log = RecognitionLog(
        plate_detected="34 ABB 123",
        is_known=False,
        confidence=0.7,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    response = client.patch(
        f"/api/logs/{log.id}/confirm",
        json={"plate_confirmed": "34 ABC 123"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    db.refresh(log)
    assert log.plate_confirmed == "34 ABC 123"
