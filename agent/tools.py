from agent.data import fetch_order

INELIGIBLE_STATUSES = {"refunded", "cancelled", "in_transit"}
REFUND_WINDOW_DAYS = 15


def get_order_status(order_id: str) -> dict:
    order = fetch_order(order_id)
    if order is None:
        return {"error": "Order not found", "order_id": order_id}
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "amount": order["amount"],
        "days_since_purchase": order["days_since_purchase"],
    }


def check_refund_eligibility(order_id: str) -> dict:
    order = fetch_order(order_id)
    if order is None:
        return {"error": "Order not found", "order_id": order_id}

    if order["status"] in INELIGIBLE_STATUSES:
        return {
            "order_id": order_id,
            "eligible": False,
            "reason": f"Order status '{order['status']}' does not allow a refund",
            "amount": order["amount"],
        }

    if order["days_since_purchase"] > REFUND_WINDOW_DAYS:
        return {
            "order_id": order_id,
            "eligible": False,
            "reason": f"Outside the {REFUND_WINDOW_DAYS}-day refund window ({order['days_since_purchase']} days since purchase)",
            "amount": order["amount"],
        }

    return {
        "order_id": order_id,
        "eligible": True,
        "reason": "Order is within the refund window and eligible for a full refund",
        "amount": order["amount"],
    }


def escalate_to_human(order_id: str, reason: str) -> dict:
    return {
        "escalated": True,
        "order_id": order_id,
        "reason": reason,
        "message": "This case has been escalated to a human agent.",
    }


if __name__ == "__main__":
    print(get_order_status("A1001"))  # happy path
    print(get_order_status("FAKE-999"))  # not found
    print(check_refund_eligibility("A1003"))  # boundary: 15 days -> eligible
    print(check_refund_eligibility("A1004"))  # boundary: 16 days -> not eligible
    print(check_refund_eligibility("A1005"))  # status: refunded -> not eligible
    print(escalate_to_human("A1001", "Customer requested manager review"))
