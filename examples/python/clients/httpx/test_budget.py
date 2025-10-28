"""
Test /acp-budget with dynamic pricing via X-Budget header.

Usage:
    uv run python test_budget.py
"""

import os
import asyncio
from dotenv import load_dotenv
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
from x402.clients.base import decode_x_payment_response

load_dotenv()

private_key = os.getenv("PRIVATE_KEY")
base_url = os.getenv("RESOURCE_SERVER_URL", "http://localhost:4021")

if not private_key:
    print("Error: PRIVATE_KEY not set")
    exit(1)

account = Account.from_key(private_key)
print(f"Account: {account.address}\n")


async def test_with_budget(budget: str):
    """Test endpoint with specific budget."""
    print(f"{'='*60}")
    print(f"Testing with budget: {budget}")
    print(f"{'='*60}")
    
    # x402HttpxClient automatically handles payment flow
    async with x402HttpxClient(
        account=account,
        base_url=base_url,
    ) as client:
        # Add X-Budget header to the request
        response = await client.get(
            "/acp-budget",
            headers={"X-Budget": budget}  # ⭐ Dynamic pricing
        )
        
        content = await response.aread()
        print(f"✅ Response: {content.decode()}")
        
        if "X-PAYMENT-RESPONSE" in response.headers:
            payment_resp = decode_x_payment_response(
                response.headers["X-PAYMENT-RESPONSE"]
            )
            print(f"🧾 TX: {payment_resp.get('transaction', 'N/A')}\n")


async def main():
    """Run tests with different budgets."""
    # await test_with_budget("$0.001")
    await test_with_budget("$0.01")
    # await test_with_budget("$0.05")


if __name__ == "__main__":
    asyncio.run(main())

