import time

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.types import ASGIApp, Receive, Scope, Send

from database.db import AsyncSessionLocal
from database.models import DBUser


class BannedUserMiddleware:
    """Safe ASGI middleware for banning users."""

    def __init__(self, app: ASGIApp, cache_ttl: int = 60):
        self.app = app
        self.cache_ttl = cache_ttl
        self.banned_cache: dict[str, tuple[bool, float]] = {}

    async def _is_banned_cached(self, user_id: str, db: AsyncSession) -> bool:
        now = time.time()
        cached = self.banned_cache.get(user_id)
        if cached and now - cached[1] < self.cache_ttl:
            return cached[0]

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return False

        result = await db.execute(select(DBUser.is_banned).where(DBUser.id == user_id_int))
        row = result.scalar_one_or_none()
        is_banned = bool(row)
        self.banned_cache[user_id] = (is_banned, now)
        return is_banned

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # ⚠️ Handle only HTTP — skip lifespan/websocket for safety
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        user_id = request.headers.get("X-User-ID")

        if user_id:
            async with AsyncSessionLocal() as session:
                if await self._is_banned_cached(user_id, session):
                    response = JSONResponse(
                        status_code=403, content={"detail": "User is banned"}
                    )
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)
