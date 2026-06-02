from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


class CompanyRepository:
    def get_by_normalized_name(
        self,
        db: Session,
        normalized_name: str,
    ) -> Company | None:
        statement = select(Company).where(
            Company.normalized_name == normalized_name
        )

        return db.scalars(statement).first()

    def create(
        self,
        db: Session,
        *,
        name: str,
        normalized_name: str,
    ) -> Company:
        company = Company(
            name=name,
            normalized_name=normalized_name,
        )

        db.add(company)
        db.flush()

        return company
