from hanuman.main import list_routes


def test_list_routes_contains_status() -> None:
    routes = list_routes()

    assert isinstance(routes, list)
    assert any("status" in route.lower() for route in routes)
