import hashlib
import hmac


def verify_razorpay_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Validates the X-Razorpay-Signature header against the raw request body.

    See: https://razorpay.com/docs/webhooks/validate-test/
    """
    if not secret or not signature:
        return False

    expected = hmac.new(secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
