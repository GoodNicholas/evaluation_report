from fastapi.testclient import TestClient

def test_metrics_endpoint(client: TestClient) -> None:
    """Test that the metrics endpoint returns valid Prometheus metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain"
    
    # Check for some expected metrics
    content = response.text
    assert "# HELP http_requests_total" in content
    assert "# TYPE http_requests_total counter" in content
    assert "# HELP http_request_duration_seconds" in content
    assert "# TYPE http_request_duration_seconds histogram" in content
    assert "# HELP user_registrations_total" in content
    assert "# TYPE user_registrations_total counter" in content
    assert "# HELP course_creations_total" in content
    assert "# TYPE course_creations_total counter" in content

def test_metrics_after_requests(client: TestClient) -> None:
    """Test that metrics are updated after making requests."""
    # Make some requests
    client.get("/health")
    client.get("/api/v1/health")
    
    # Check metrics
    response = client.get("/metrics")
    content = response.text
    
    # Should see metrics for the requests we made
    assert 'http_requests_total{method="GET",endpoint="/health",status="200"}' in content
    assert 'http_requests_total{method="GET",endpoint="/api/v1/health",status="200"}' in content
    assert 'http_request_duration_seconds_bucket{method="GET",endpoint="/health"' in content
    assert 'http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/health"' in content 