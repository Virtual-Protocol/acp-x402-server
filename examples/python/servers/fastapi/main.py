import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from x402.fastapi.middleware import require_payment
from x402.types import EIP712Domain, TokenAmount, TokenAsset
from cdp.auth import generate_jwt, JwtOptions

# Configure logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Get configuration from environment
ADDRESS = os.getenv("ADDRESS")
CDP_API_KEY_ID = os.getenv("CDP_API_KEY_ID")
CDP_API_KEY_SECRET = os.getenv("CDP_API_KEY_SECRET")
NETWORK = os.getenv("NETWORK")

print(f"🔍 Loading environment variables:")
print(f"   ADDRESS: {ADDRESS}")
print(f"   CDP_API_KEY_ID: {CDP_API_KEY_ID[:20] if CDP_API_KEY_ID else 'NOT SET'}...")
print(f"   CDP_API_KEY_SECRET: {'SET' if CDP_API_KEY_SECRET else 'NOT SET'} ({len(CDP_API_KEY_SECRET) if CDP_API_KEY_SECRET else 0} chars)")

if not ADDRESS:
    raise ValueError("Missing required environment variable: ADDRESS")
if not NETWORK or NETWORK not in ["base", "base-sepolia"]:
    raise ValueError(f"Invalid network: {NETWORK}")

app = FastAPI()


# Coinbase Facilitator configuration
def create_cdp_auth_headers():
    """Create CDP authentication headers for Coinbase facilitator using official CDP SDK"""
    if not CDP_API_KEY_ID or not CDP_API_KEY_SECRET:
        # Fall back to default facilitator if no CDP credentials
        return None
    
    async def async_create_headers():
        request_host = "api.cdp.coinbase.com"
        
        # Use official CDP SDK to create JWT tokens
        verify_options = JwtOptions(
            api_key_id=CDP_API_KEY_ID,
            api_key_secret=CDP_API_KEY_SECRET,
            request_method="POST",
            request_host=request_host,
            request_path="/platform/v2/x402/verify",
        )
        verify_jwt = generate_jwt(verify_options)
        
        settle_options = JwtOptions(
            api_key_id=CDP_API_KEY_ID,
            api_key_secret=CDP_API_KEY_SECRET,
            request_method="POST",
            request_host=request_host,
            request_path="/platform/v2/x402/settle",
        )
        settle_jwt = generate_jwt(settle_options)
        
        # Add Correlation-Context header as required by CDP API
        correlation_context = "sdk_version=1.33.1,sdk_language=python,source=x402,source_version=0.6.6"
        
        return {
            "verify": {
                "Authorization": f"Bearer {verify_jwt}",
                "Correlation-Context": correlation_context,
            },
            "settle": {
                "Authorization": f"Bearer {settle_jwt}",
                "Correlation-Context": correlation_context,
            },
        }
    
    return async_create_headers


# Determine facilitator config
facilitator_config = None
if CDP_API_KEY_ID and CDP_API_KEY_SECRET:
    facilitator_config = {
        "url": "https://api.cdp.coinbase.com/platform/v2/x402",
        "create_headers": create_cdp_auth_headers(),
    }
    print("✅ Using Coinbase CDP Facilitator")
else:
    print("⚠️  Using default facilitator (x402.org) - may have issues with mainnet")
    print("   To use Coinbase facilitator, set CDP_API_KEY_ID and CDP_API_KEY_SECRET")


# Custom dynamic pricing middleware for /acp-budget
async def dynamic_price_middleware(request: Request, call_next):
    """Middleware that reads price from X-Budget header"""
    if not request.url.path.startswith("/acp-budget"):
        return await call_next(request)
    
    # Read dynamic price from X-Budget header
    budget = request.headers.get("X-Budget", "$0.001")
    print(f"📋 Dynamic budget from header: {budget}")
    
    # Use the standard require_payment middleware with dynamic price
    payment_middleware = require_payment(
        path="/acp-budget",
        price=budget,  # ⭐ dynamic price
        pay_to_address=ADDRESS,
        network=NETWORK,
        facilitator_config=facilitator_config,
        description=f"$pong token access ({budget})",
        mime_type="application/json",
    )
    
    return await payment_middleware(request, call_next)

# Apply dynamic pricing middleware
app.middleware("http")(dynamic_price_middleware)

# # Apply payment middleware to premium routes
# app.middleware("http")(
#     require_payment(
#         path="/premium/*",
#         price=TokenAmount(
#             amount="10000",
#             asset=TokenAsset(
#                 address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
#                 decimals=6,
#                 eip712=EIP712Domain(name="USDC", version="2"),
#             ),
#         ),
#         pay_to_address=ADDRESS,
#         network=NETWORK,
#     )
# )


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.get("/acp-budget")
async def acp_budget() -> Dict[str, Any]:
    return {
        "message": "pay acp job budget",
        "token": "acp job payment token",
        "protocol": "x402",
        "utility": "none",
        "vibes": "acp early adopter",
        "advice": "not financial advice"
    }


# @app.get("/premium/content")
# async def get_premium_content() -> Dict[str, Any]:
#     return {
#         "content": "This is premium content",
#     }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)
