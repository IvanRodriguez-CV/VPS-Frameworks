from datetime import datetime, timedelta, timezone

import jwt

from config.segurity import ALGORITHM, SECRET_KEY_TOKEN

ADMIN_USERNAME = "admin_pruebas"
ADMIN_PASSWORD = "AdminPruebas123"


def login(client, username: str = ADMIN_USERNAME, password: str = ADMIN_PASSWORD):
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_book(client, headers):
    author = client.post("/authors/", json={"name": "Autora de prueba"}, headers=headers)
    category = client.post(
        "/categories/", json={"name": "Narrativa de prueba"}, headers=headers
    )
    assert author.status_code == 201
    assert category.status_code == 201
    book = client.post(
        "/books/",
        json={
            "title": "Libro de prueba",
            "description": "Descripción",
            "author_id": author.json()["id"],
            "category_id": category.json()["id"],
        },
        headers=headers,
    )
    assert book.status_code == 201
    return book.json(), author.json(), category.json()


def test_login_and_protected_catalog(client):
    headers = login(client)
    current_user = client.get("/auth/me", headers=headers)
    assert current_user.status_code == 200
    assert "password" not in current_user.json()
    assert "password_hash" not in current_user.json()
    login_response = client.post(
        "/auth/login",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert "email" not in login_response.json()["user"]
    assert client.get("/books/", headers=headers).status_code == 200
    assert client.get("/books/").status_code == 401


def test_invalid_credentials_do_not_reveal_user(client):
    response = client.post(
        "/auth/login",
        data={"username": "no_existe", "password": "incorrecta"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas."


def test_invalid_and_expired_tokens_are_rejected(client):
    assert client.get(
        "/categories/", headers={"Authorization": "Bearer token-invalido"}
    ).status_code == 401

    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY_TOKEN,
        algorithm=ALGORITHM,
    )
    response = client.get(
        "/categories/", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


def test_regular_user_cannot_manage_catalog_or_change_role(client):
    registration = client.post(
        "/auth/register",
        json={
            "username": "lector_prueba",
            "nombre": "Lector",
            "apellido": "Prueba",
            "email": "lector@example.com",
            "password": "LectorPrueba123",
        },
    )
    assert registration.status_code == 201
    user_headers = login(client, "lector_prueba", "LectorPrueba123")
    assert (
        client.post(
            "/authors/", json={"name": "Sin permiso"}, headers=user_headers
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/users/{registration.json()['id']}",
            json={"role_id": 1},
            headers=user_headers,
        ).status_code
        == 403
    )


def test_catalog_crud_and_referential_integrity(client):
    headers = login(client)
    book, author, category = create_book(client, headers)

    listed = client.get("/books/", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == book["id"]

    updated = client.patch(
        f"/books/{book['id']}",
        json={"title": "Libro actualizado"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Libro actualizado"

    assert (
        client.delete(f"/books/{book['id']}", headers=headers).status_code == 409
    )
    copies = client.get(f"/books/{book['id']}/copies", headers=headers)
    assert copies.status_code == 200
    assert len(copies.json()) == 1
    copy_id = copies.json()[0]["id"]
    assert client.delete(f"/copies/{copy_id}", headers=headers).status_code == 204
    assert client.delete(f"/books/{book['id']}", headers=headers).status_code == 204
    assert (
        client.delete(f"/categories/{category['id']}", headers=headers).status_code
        == 204
    )
    assert (
        client.delete(f"/authors/{author['id']}", headers=headers).status_code == 204
    )


def test_loan_makes_copy_unavailable_then_returned_again(client):
    headers = login(client)
    book, _, _ = create_book(client, headers)
    copy = client.get(f"/books/{book['id']}/copies", headers=headers).json()[0]
    loan_response = client.post(
        "/loans/",
        json={
            "copy_id": copy["id"],
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
        headers=headers,
    )
    assert loan_response.status_code == 201
    loan = loan_response.json()
    assert loan["book_id"] == book["id"]
    assert loan["status"] == "active"
    assert (
        client.post(
            "/loans/",
            json={
                "copy_id": copy["id"],
                "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
            headers=headers,
        ).status_code
        == 409
    )

    returned = client.post(f"/loans/{loan['id']}/return", headers=headers)
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned"
    assert client.get(f"/books/{book['id']}/copies", headers=headers).json()[0][
        "is_available"
    ]
    assert client.post(f"/loans/{loan['id']}/return", headers=headers).status_code == 409


def test_invalid_input_is_rejected(client):
    headers = login(client)
    assert (
        client.post(
            "/auth/register",
            json={
                "username": "usuario_invalido",
                "nombre": "Nombre",
                "apellido": "Apellido",
                "email": "no-es-correo",
                "password": "clave1234",
            },
        ).status_code
        == 422
    )
    assert (
        client.post("/authors/", json={"name": " "}, headers=headers).status_code
        == 422
    )

    book, _, _ = create_book(client, headers)
    copy = client.get(f"/books/{book['id']}/copies", headers=headers).json()[0]
    past_due_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert (
        client.post(
            "/loans/",
            json={"copy_id": copy["id"], "due_date": past_due_date},
            headers=headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/loans/",
            json={"copy_id": copy["id"], "due_date": "2027-01-15T17:00:00"},
            headers=headers,
        ).status_code
        == 422
    )


def test_admin_user_and_role_management(client):
    headers = login(client)
    roles = client.get("/roles/", headers=headers)
    assert roles.status_code == 200
    librarian_role = next(role for role in roles.json() if role["name"] == "librarian")
    created = client.post(
        "/users/",
        json={
            "username": "bibliotecario_prueba",
            "nombre": "Bibliotecario",
            "apellido": "Prueba",
            "email": "bibliotecario@example.com",
            "password": "Bibliotecario123",
            "role_id": librarian_role["id"],
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["role"] == "librarian"
    assert client.get("/users/", headers=headers).status_code == 200
