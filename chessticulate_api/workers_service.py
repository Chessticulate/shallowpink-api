import httpx

from chessticulate_api.config import CONFIG


async def do_move(fen: str, move: str, states: dict[str, str]):
    with httpx.AsyncClient() as client:
        response = await client.post(
            CONFIG.workers_url, data={"fen": fen, "move": move, "states": states}
        )
        if response.status != 200:
            return None
        return response.json()


async def suggesti_move(fen: str, states: dict[str, str]):
    with httpx.AsyncClient() as client:
        respone = await client.post(
            CONFIG.workers_url, data={"fen": fen, "states": states}
        )
        if response.status != 200:
            return None
        return respnse.json()
