from __future__ import annotations
def create_support_case_schema():
    return {
        "type": "object",
        "required": ["customer_id", "reason", "amount", "currency"],
        "properties": {
            "customer_id": {"type": "string", "minLength": 3},
            "reason": {"type": "string", "enum": ["duplicate_debit","merchant_error","fraud_review"]},
            "amount": {"type": "number", "minimum": 0},
            "currency": {"type": "string", "minLength": 3, "maxLength": 3}
        },
        "additionalProperties": False
    }
SCHEMAS = {
    "create_support_case": create_support_case_schema()
}
