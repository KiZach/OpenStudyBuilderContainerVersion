def test_get_system_information(api_client):
    response = api_client.get("/system/information")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get(
        "api_version"
    ), "missing api_version property of system information"
    assert payload.get(
        "db_version"
    ), "missing db_version property of system information"
    assert payload.get("build_id"), "missing build_id property of system information"


def test_get_system_healthcheck(api_client):
    response = api_client.get("/system/healthcheck")
    assert response.status_code == 200


def test_get_system_information_build_id(api_client):
    response = api_client.get("/system/information/build-id")
    assert response.status_code == 200
    assert response.text
