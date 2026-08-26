from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.models.customer import Customer
from app.schemas.customer import CustomerConsentUpdate, CustomerRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, Customer, customer_id, "customer")


@router.patch("/{customer_id}/consent", response_model=CustomerRead)
def update_consent(customer_id: str, body: CustomerConsentUpdate, db: Session = Depends(get_db)):
    customer = get_or_404(db, Customer, customer_id, "customer")

    if body.contact_consent is not None:
        customer.contact_consent = body.contact_consent.model_dump()
    if body.contact_quiet_hours is not None:
        customer.contact_quiet_hours = body.contact_quiet_hours.model_dump()
    if body.opted_out is not None:
        customer.opted_out = body.opted_out

    db.commit()
    db.refresh(customer)
    return customer
