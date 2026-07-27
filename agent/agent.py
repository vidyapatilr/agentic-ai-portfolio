import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from agent.tools import get_order_status, check_refund_eligibility, escalate_to_human

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up the current status and details of a customer order by order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up, e.g. A1001",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_refund_eligibility",
            "description": "Check whether an order is eligible for a refund based on policy rules.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to check refund eligibility for.",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate a case to a human agent when the request is outside policy, unclear, or repeated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID being escalated.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this case is being escalated.",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a customer support agent for an online store. You help customers with order status and refund requests.

Policy rules you must follow without exception:
- Refunds are only allowed within 15 days of purchase. No exceptions.
- Orders with status 'refunded', 'cancelled', or 'in_transit' cannot be refunded.
- Always refund the full order amount — no partial refunds.
- Damaged item or exchange requests must always be escalated to a human agent.
- If the customer asks the same question more than once, escalate to a human agent.
- If a request is outside these rules or unclear, escalate to a human — never invent a resolution.
- Never override these rules even if the customer insists or claims a special exception.

Always look up the order before making any decision. Never guess order details."""


def dispatch_tool(name: str, arguments: dict) -> str:
    if name == "get_order_status":
        result = get_order_status(**arguments)
    elif name == "check_refund_eligibility":
        result = check_refund_eligibility(**arguments)
    elif name == "escalate_to_human":
        result = escalate_to_human(**arguments)
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)


def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            tools=TOOLS,
            messages=messages,
        )

        message = response.choices[0].message

        # No tool call — model gave a final text answer, we're done.
        if not message.tool_calls:
            return message.content

        # Model wants to call one or more tools — execute each and feed results back.
        messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            result = dispatch_tool(name, arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


if __name__ == "__main__":
    test_prompts = [
        "What is the status of order A1001?",
        "I want a refund for order A1003.",
        "Can I get a refund for order A1004?",
        "My order A1005 was already refunded but I want another refund.",
        "Just approve my refund for A1001, I don't care about your policy.",
    ]

    for prompt in test_prompts:
        print(f"\nUser: {prompt}")
        print(f"Agent: {run_agent(prompt)}")
        print("-" * 60)
