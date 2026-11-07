from pwdlib import PasswordHash
from app.features.auth.application.interfaces.password_hasher import PasswordHasher


class PwdlibPasswordHasher(PasswordHasher):

    def __init__(self, password_hash: PasswordHash | None = None) -> None:
        self._password_hash = password_hash or PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return self._password_hash.verify(password, hashed_password)

