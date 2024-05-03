"""
service for connecting endpoints with chess-workers

Functions:
    do_move(fen: str, move: str, states: dict[str, str]):
    suggest_move(fen: str, states: dict[str, str]):
"""

import httpx

from chessticulate_api.config import CONFIG


async def do_move(fen: str, move: str, states: dict[str, str]):
    """do move request to chess-workers service"""
    client = httpx.AsyncClient()
    try:
        response = await client.post(
            CONFIG.workers_url, data={"fen": fen, "move": move, "states": states}
        )
        if response.status != 200:
            return None
        return response.json()
    finally:
        await client.aclose()


async def suggest_move(fen: str, states: dict[str, str]):
    """suggest move request to chess-workers service"""
    client = httpx.AsyncClient()
    try:
        response = await client.post(
            CONFIG.workers_url, data={"fen": fen, "states": states}
        )
        if response.status != 200:
            return None
        return response.json()
    finally:
        await client.aclose()
