from app import app


def test_home_page():
    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200


def test_login_page():
    client = app.test_client()
    response = client.get('/login')

    assert response.status_code == 200


def test_forgot_password_page():
    client = app.test_client()
    response = client.get('/forgot-password')

    assert response.status_code == 200


def test_dashboard_redirect():
    client = app.test_client()
    response = client.get('/dashboard')

    assert response.status_code in [200, 302]


def test_regenerate_meal_route():
    client = app.test_client()

    response = client.post(
        '/regenerate-meal',
        json={
            'meal_type': 'breakfast'
        }
    )

    assert response.status_code in [200, 302, 400]