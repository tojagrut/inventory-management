"""
Tests for reports API endpoints (quarterly and monthly trends).
"""
import pytest


def _orders(client, query=""):
    return client.get(f"/api/orders{query}").json()


class TestQuarterlyReportsEndpoints:
    """Test suite for /api/reports/quarterly."""

    def test_get_all_quarterly_reports(self, client):
        """Test getting quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for q in data:
            for field in ["quarter", "total_orders", "total_revenue",
                          "delivered_orders", "avg_order_value", "fulfillment_rate"]:
                assert field in q
            assert isinstance(q["total_orders"], int)
            assert isinstance(q["total_revenue"], (int, float))
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_reports_sorted(self, client):
        """Test that quarters come back in order."""
        data = client.get("/api/reports/quarterly").json()
        quarters = [q["quarter"] for q in data]
        assert quarters == sorted(quarters)

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly totals add up to the orders endpoint."""
        data = client.get("/api/reports/quarterly").json()
        orders = _orders(client)

        assert sum(q["total_orders"] for q in data) == len(orders)
        assert abs(sum(q["total_revenue"] for q in data)
                   - sum(o["total_value"] for o in orders)) < 0.05

    def test_quarterly_revenue_rounded_to_cents(self, client):
        """Test that revenue values carry no float noise beyond 2 decimals."""
        for q in client.get("/api/reports/quarterly").json():
            assert round(q["total_revenue"], 2) == q["total_revenue"]
            assert round(q["avg_order_value"], 2) == q["avg_order_value"]

    def test_get_quarterly_reports_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        data = client.get("/api/reports/quarterly?warehouse=Tokyo").json()
        expected = _orders(client, "?warehouse=Tokyo")
        assert sum(q["total_orders"] for q in data) == len(expected)

    def test_get_quarterly_reports_by_month(self, client):
        """Test that a month filter leaves only that month's quarter."""
        data = client.get("/api/reports/quarterly?month=2025-05").json()
        assert [q["quarter"] for q in data] == ["Q2-2025"]
        assert data[0]["total_orders"] == len(_orders(client, "?month=2025-05"))

    def test_get_quarterly_reports_multiple_filters(self, client):
        """Test filtering quarterly reports with several filters at once."""
        query = "?warehouse=San Francisco&category=Sensors&status=Delivered"
        data = client.get(f"/api/reports/quarterly{query}").json()
        expected = _orders(client, query)

        assert sum(q["total_orders"] for q in data) == len(expected)
        # Every order in the result is Delivered, so fulfillment is 100%
        for q in data:
            assert q["fulfillment_rate"] == 100.0

    def test_quarterly_reports_no_matches(self, client):
        """Test that filters matching nothing return an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []

    def test_quarterly_reports_all_values_ignored(self, client):
        """Test that 'all' filter values behave like no filter."""
        unfiltered = client.get("/api/reports/quarterly").json()
        all_values = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert all_values == unfiltered


class TestMonthlyTrendsEndpoints:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_all_monthly_trends(self, client):
        """Test getting monthly trends without filters."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for m in data:
            for field in ["month", "order_count", "revenue", "delivered_count"]:
                assert field in m
            assert len(m["month"]) == 7 and m["month"][4] == "-"
            assert m["delivered_count"] <= m["order_count"]
            assert round(m["revenue"], 2) == m["revenue"]

    def test_monthly_trends_sorted(self, client):
        """Test that months come back in order."""
        months = [m["month"] for m in client.get("/api/reports/monthly-trends").json()]
        assert months == sorted(months)

    def test_get_monthly_trends_by_category(self, client):
        """Test filtering monthly trends by category."""
        data = client.get("/api/reports/monthly-trends?category=Sensors").json()
        expected = _orders(client, "?category=Sensors")
        assert sum(m["order_count"] for m in data) == len(expected)

    def test_get_monthly_trends_by_status(self, client):
        """Test filtering monthly trends by status."""
        data = client.get("/api/reports/monthly-trends?status=Shipped").json()
        assert len(data) > 0
        for m in data:
            assert m["delivered_count"] == 0

    def test_get_monthly_trends_by_quarter(self, client):
        """Test that a quarter filter keeps only that quarter's months."""
        data = client.get("/api/reports/monthly-trends?month=Q3-2025").json()
        assert {m["month"] for m in data} <= {"2025-07", "2025-08", "2025-09"}
        assert len(data) > 0
