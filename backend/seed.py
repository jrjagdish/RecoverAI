"""Seeds synthetic customers/payments, runs them through a batch, and executes
allowed attempts — so the dashboard has something to show immediately.

Usage: python seed.py (run from the backend/ directory, with the venv active)
"""

from datetime import datetime

from app.database import Base, SessionLocal, engine
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import PolicyDecision
from app.models.recovery_batch import BatchStatus, RecoveryBatch
from app.services import recovery_engine

Base.metadata.create_all(bind=engine)

SEED_CUSTOMERS = [
    {"name": "Asha Rao", "email": "asha@example.com", "phone": "+919800000001"},
    {"name": "Vikram Shah", "email": "vikram@example.com", "phone": "+919800000002"},
    {"name": "Priya Nair", "email": "priya@example.com", "phone": "+919800000003", "opted_out": True},
    {"name": "Rohit Verma", "email": "rohit@example.com", "phone": "+919800000004"},
]

SEED_PAYMENTS = [
    {"customer": 0, "amount": 1499, "failure_reason": "insufficient_funds"},
    {"customer": 1, "amount": 899, "failure_reason": "upi_timeout"},
    {"customer": 2, "amount": 2200, "failure_reason": "insufficient_funds"},  # opted out -> policy should block
    {"customer": 3, "amount": 20, "failure_reason": "network_error"},  # below cost-to-recover -> stop
]


def run():
    db = SessionLocal()
    try:
        customers = []
        for c in SEED_CUSTOMERS:
            existing = db.query(Customer).filter(Customer.email == c["email"]).first()
            if existing:
                customers.append(existing)
                continue
            customer = Customer(
                name=c["name"],
                email=c["email"],
                phone=c["phone"],
                opted_out=c.get("opted_out", False),
            )
            db.add(customer)
            db.flush()
            customers.append(customer)

        batch = RecoveryBatch(name=f"Seed batch {datetime.utcnow():%Y-%m-%d %H:%M}", status=BatchStatus.RUNNING)
        db.add(batch)
        db.flush()

        for p in SEED_PAYMENTS:
            payment = Payment(
                customer_id=customers[p["customer"]].id,
                amount=p["amount"],
                status=PaymentStatus.FAILED,
                failure_reason=p["failure_reason"],
                batch_id=batch.id,
            )
            db.add(payment)
            db.flush()

            batch.total_amount_at_risk += payment.amount
            batch.total_payments_count += 1

            attempt = recovery_engine.evaluate(db, payment)
            if attempt.policy_decision == PolicyDecision.ALLOWED:
                recovery_engine.execute(db, attempt)

        db.commit()
        print(f"Seeded batch {batch.id} with {len(SEED_PAYMENTS)} payments.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
