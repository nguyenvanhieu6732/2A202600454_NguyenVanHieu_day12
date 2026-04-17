from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API Key provided in the X-API-Key header.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Include header: X-API-Key: <your-key>",
        )
    
    if api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key.",
        )
    
    return api_key
