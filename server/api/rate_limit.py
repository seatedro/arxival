from fastapi import Request
import asyncio


async def rate_limit(request: Request):
    # TODO: Placeholder for proper rate limiting
    await asyncio.sleep(0.1)
