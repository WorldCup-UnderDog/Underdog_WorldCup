"""Compose v1 endpoint routers."""

from fastapi import APIRouter

from .endpoints import darkscore, health, players, predict, teams

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(teams.router, tags=["teams"])
api_router.include_router(predict.router, tags=["predict"])
api_router.include_router(players.router, tags=["players"])
api_router.include_router(darkscore.router, tags=["darkscore"])

