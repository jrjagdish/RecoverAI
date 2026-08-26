from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db  # re-exported for convenience

__all__ = ["get_db", "get_or_404"]


def get_or_404(db: Session, model, id_: str, name: str = "resource"):
    obj = db.get(model, id_)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj
