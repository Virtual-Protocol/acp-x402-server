from typing import Literal


SupportedNetworks = Literal["base", "base-sepolia", "avalanche-fuji", "avalanche"]

EVM_NETWORK_TO_CHAIN_ID = {
    "base-sepolia": 84532,
    "base": 8453,
    "avalanche-fuji": 43113,
    "avalanche": 43114,
}

# CAIP-2 format mapping (eip155:chainId -> network name)
CAIP2_TO_NETWORK = {
    "eip155:84532": "base-sepolia",
    "eip155:8453": "base",
    "eip155:43113": "avalanche-fuji",
    "eip155:43114": "avalanche",
}

# Chain ID to network name mapping
CHAIN_ID_TO_NETWORK = {
    84532: "base-sepolia",
    8453: "base",
    43113: "avalanche-fuji",
    43114: "avalanche",
}


def normalize_network(network: str) -> str:
    """
    Normalize network identifier to standard format.
    
    Accepts:
    - Standard format: "base", "base-sepolia", etc.
    - CAIP-2 format: "eip155:8453", "eip155:84532", etc.
    - Chain ID: "8453", "84532", etc.
    
    Returns:
        Normalized network name in standard format
        
    Raises:
        ValueError: If network format is not recognized
    """
    # Already in standard format
    if network in ["base", "base-sepolia", "avalanche-fuji", "avalanche"]:
        return network
    
    # CAIP-2 format (eip155:chainId)
    if network.startswith("eip155:"):
        normalized = CAIP2_TO_NETWORK.get(network)
        if normalized:
            return normalized
        raise ValueError(f"Unsupported CAIP-2 network: {network}")
    
    # Try as chain ID
    try:
        chain_id = int(network)
        normalized = CHAIN_ID_TO_NETWORK.get(chain_id)
        if normalized:
            return normalized
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    except ValueError:
        pass
    
    raise ValueError(f"Unsupported network format: {network}")
