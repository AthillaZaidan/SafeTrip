from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.orm import Officer


class OfficerService:
    def __init__(self, db: Session):
        self.db = db

    def list_officers(self, status: str | None = None) -> list[Officer]:
        q = self.db.query(Officer)
        if status:
            q = q.filter(Officer.status == status)
        return q.all()

    def get_officer(self, officer_id: str) -> Officer | None:
        return self.db.query(Officer).filter(Officer.officer_id == officer_id).first()

    def recommend(self, incident_location: str = "", count: int = 1) -> list[dict]:
        available = self.db.query(Officer).filter(Officer.status == "available").all()
        results = []
        for o in available[:count]:
            results.append({
                "officer_id": o.officer_id,
                "name": o.name,
                "role": o.role,
                "location": o.location,
                "status": o.status,
                "distance": 0.0,
            })
        return results
