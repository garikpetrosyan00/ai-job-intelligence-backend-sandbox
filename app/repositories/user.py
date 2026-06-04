from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)

        return db.scalars(statement).first()

    def get_by_email(self, db: Session, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        return db.scalars(statement).first()

    def create(
        self,
        db: Session,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )

        db.add(user)
        db.flush()

        return user
