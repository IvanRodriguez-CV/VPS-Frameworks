from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return password_context.verify(plain_password, hashed_password)
