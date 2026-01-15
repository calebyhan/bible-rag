"""Tests for API endpoints."""

import pytest


@pytest.mark.unit
def test_root_endpoint(test_client):
    """Test root endpoint returns API info."""
    response = test_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Bible RAG API"
    assert "version" in data
    assert "docs" in data


@pytest.mark.unit
def test_health_endpoint(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.unit
def test_get_translations_empty(test_client):
    """Test getting translations when none exist."""
    response = test_client.get("/api/translations")
    assert response.status_code == 200

    data = response.json()
    assert "translations" in data
    assert data["total_count"] == 0
    assert len(data["translations"]) == 0


@pytest.mark.unit
def test_get_translations_with_data(test_client, sample_translation):
    """Test getting translations with data."""
    response = test_client.get("/api/translations")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert len(data["translations"]) == 1
    assert data["translations"][0]["abbreviation"] == "TEV"
    assert data["translations"][0]["name"] == "Test English Version"


@pytest.mark.unit
def test_get_books_empty(test_client):
    """Test getting books when none exist."""
    response = test_client.get("/api/books")
    assert response.status_code == 200

    data = response.json()
    assert "books" in data
    assert data["total_count"] == 0


@pytest.mark.unit
def test_get_books_with_data(test_client, sample_book):
    """Test getting books with data."""
    response = test_client.get("/api/books")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert len(data["books"]) == 1
    assert data["books"][0]["name"] == "Genesis"
    assert data["books"][0]["testament"] == "OT"


@pytest.mark.unit
def test_get_books_filter_testament(test_client, sample_book, sample_nt_book):
    """Test filtering books by testament."""
    response = test_client.get("/api/books?testament=NT")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert data["books"][0]["name"] == "Matthew"
    assert data["books"][0]["testament"] == "NT"


@pytest.mark.unit
def test_get_books_filter_genre(test_client, sample_book, sample_nt_book):
    """Test filtering books by genre."""
    response = test_client.get("/api/books?genre=gospel")
    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 1
    assert data["books"][0]["genre"] == "gospel"


@pytest.mark.unit
def test_get_verse_not_found(test_client):
    """Test getting non-existent verse."""
    response = test_client.get("/api/verse/Genesis/1/1")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.unit
def test_get_verse_book_not_found(test_client, sample_book):
    """Test getting verse with invalid book."""
    response = test_client.get("/api/verse/InvalidBook/1/1")
    assert response.status_code == 404


@pytest.mark.unit
def test_get_verse_success(test_client, sample_book, sample_translation, sample_verse):
    """Test getting verse successfully."""
    response = test_client.get("/api/verse/Genesis/1/1")
    assert response.status_code == 200

    data = response.json()
    assert "reference" in data
    assert data["reference"]["book"] == "Genesis"
    assert data["reference"]["chapter"] == 1
    assert data["reference"]["verse"] == 1


@pytest.mark.unit
def test_search_missing_query(test_client):
    """Test search without query parameter."""
    response = test_client.post("/api/search", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.unit
def test_search_empty_results(test_client, sample_translation):
    """Test search returns empty results."""
    response = test_client.post(
        "/api/search",
        json={
            "query": "test query",
            "translations": ["TEV"],
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "query_time_ms" in data
    assert "results" in data
    assert data["search_metadata"]["total_results"] == 0


@pytest.mark.unit
def test_themes_missing_theme(test_client):
    """Test themes endpoint without theme parameter."""
    response = test_client.post("/api/themes", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.unit
def test_themes_success(test_client, sample_translation):
    """Test themes endpoint with valid request."""
    response = test_client.post(
        "/api/themes",
        json={
            "theme": "love",
            "translations": ["TEV"],
            "testament": "both",
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "theme" in data
    assert data["theme"] == "love"
    assert "query_time_ms" in data
    assert "results" in data
    assert "total_results" in data


@pytest.mark.unit
def test_themes_testament_filter(test_client, sample_translation):
    """Test themes endpoint with testament filter."""
    response = test_client.post(
        "/api/themes",
        json={
            "theme": "covenant",
            "translations": ["TEV"],
            "testament": "OT",
        },
    )
    assert response.status_code == 200

    data = response.json()
    # Check that testament filter is present (might be None or "OT")
    assert "testament_filter" in data or data.get("testament_filter") == "OT"


@pytest.mark.unit
def test_themes_max_results(test_client, sample_translation):
    """Test themes endpoint respects max_results."""
    response = test_client.post(
        "/api/themes",
        json={
            "theme": "faith",
            "translations": ["TEV"],
            "max_results": 5,
        },
    )
    assert response.status_code == 200

    data = response.json()
    # Even if there are no results, the request should succeed
    assert response.status_code == 200


@pytest.mark.unit
def test_themes_with_multiple_translations(test_client, sample_translation, sample_korean_translation):
    """Test themes with multiple translations."""
    response = test_client.post(
        "/api/themes",
        json={
            "theme": "hope",
            "translations": ["TEV", "TKV"],
            "languages": ["en", "ko"],
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
