from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.models.audit_log import AuditLog
from app.models.payment import Payment
from app.models.recovery_batch import RecoveryBatch
from app.schemas.audit import AuditLogRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/payment/{payment_id}", response_model=list[AuditLogRead])
def get_payment_audit_trail(payment_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Payment, payment_id, "payment")
    return (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "payment", AuditLog.entity_id == payment_id)
        .order_by(AuditLog.created_at)
        .all()
    )


@router.get("/batch/{batch_id}", response_model=list[AuditLogRead])
def get_batch_audit_trail(batch_id: str, db: Session = Depends(get_db)):
    get_or_404(db, RecoveryBatch, batch_id, "batch")
    payment_ids = [p.id for p in db.query(Payment.id).filter(Payment.batch_id == batch_id).all()]
    return (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "payment", AuditLog.entity_id.in_(payment_ids))
        .order_by(AuditLog.created_at)
        .all()
    )
