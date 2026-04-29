import pytest
from ez_wechatblog.server import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestServerHealth:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "EZ_WeChatBlog API"
        assert "endpoints" in data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestServerListEndpoints:
    def test_list_publishers(self, client):
        resp = client.get("/publishers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "local" in data["publishers"]
        assert "hugo" in data["publishers"]
        assert "hexo" in data["publishers"]

    def test_list_fetchers(self, client):
        resp = client.get("/fetchers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "playwright" in data["fetchers"]
        assert "camoufox" in data["fetchers"]

    def test_list_templates(self, client):
        resp = client.get("/templates")
        assert resp.status_code == 200
        data = resp.get_json()
        names = [t["name"] for t in data["templates"]]
        assert "markdown" in names
        assert "html" in names


class TestServerConvert:
    def test_convert_missing_url(self, client):
        resp = client.post("/convert", json={})
        assert resp.status_code == 400
        assert "url" in resp.get_json()["error"].lower()

    def test_convert_invalid_url(self, client):
        resp = client.post("/convert", json={"url": "not a url"})
        assert resp.status_code == 400

    def test_convert_empty_url(self, client):
        resp = client.post("/convert", json={"url": ""})
        assert resp.status_code == 400

    def test_convert_no_json(self, client):
        resp = client.post("/convert")
        assert resp.status_code == 400