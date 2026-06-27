from app.core.responses import success


def test_success_response_shape():
    assert success({"ok": True}) == {"code": 0, "message": "success", "data": {"ok": True}}
