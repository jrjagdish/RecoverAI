from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactConsent(BaseModel):
    email: bool = True
    sms: bool = False
    call: bool = False


class QuietHours(BaseModel):
    start: str = "21:00"
    end: str = "09:00"
    timezone: str = "Asia/Kolkata"


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    phone: str | None
    contact_consent: dict
    contact_quiet_hours: dict
    opted_out: bool
    created_at: datetime


class CustomerConsentUpdate(BaseModel):
    contact_consent: ContactConsent | None = None
    contact_quiet_hours: QuietHours | None = None
    opted_out: bool | None = None
