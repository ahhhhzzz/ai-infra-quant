from fastapi import APIRouter

from ai_infra_quant.backend.api.v1 import (
    brokers,
    market_data,
    paqs_e,
    paqs_market_snapshot,
    performance,
    portfolio,
    positions,
    providers,
    securities,
    strategies,
    watchlist,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(portfolio.router)
api_router.include_router(positions.router)
api_router.include_router(performance.router)
api_router.include_router(watchlist.router)
api_router.include_router(securities.router)
api_router.include_router(strategies.router)
api_router.include_router(brokers.router)
api_router.include_router(providers.router)
api_router.include_router(market_data.router)
api_router.include_router(paqs_market_snapshot.router)
api_router.include_router(paqs_e.router)
