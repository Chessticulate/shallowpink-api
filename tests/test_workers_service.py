import json

import httpx
import pytest
import respx

from chessticulate_api import workers_service
from chessticulate_api.config import CONFIG


class TestDoMove:
    @pytest.mark.parametrize(
        "response_content",
        [
            {"content": json.dumps({"message": "invalid move"}).encode()},
            {"content": json.dumps({"message": "player is still in check"}).encode()},
            {"content": json.dumps({"message": "move puts player in check"}).encode()},
        ],
    )
    @pytest.mark.asyncio
    async def test_do_move_client_request_exception(self, response_content):
        with respx.mock:
            respx.post(CONFIG.workers_url).mock(
                return_value=httpx.Response(400, **response_content)
            )

            with pytest.raises(workers_service.ClientRequestError):
                await workers_service.do_move(fen="fen", move="move", states={})

    @pytest.mark.parametrize(
        "response_content",
        [
            {"content": json.dumps({"message": "Internal Server Error"}).encode()},
        ],
    )
    @pytest.mark.asyncio
    async def test_do_move_server_request_exception(self, response_content):
        with respx.mock:
            respx.post(CONFIG.workers_url).mock(
                return_value=httpx.Response(500, **response_content)
            )

            with pytest.raises(workers_service.ServerRequestError):
                await workers_service.do_move(fen="fen", move="move", states={})


class TestSuggestMove:

    @pytest.mark.parametrize(
        "response_content",
        [
            {"content": json.dumps({"message": "the game is already over"}).encode()},
        ],
    )
    @pytest.mark.asyncio
    async def test_suggest_move_client_request_exception(self, response_content):
        with respx.mock:
            respx.post(CONFIG.workers_url).mock(
                return_value=httpx.Response(400, **response_content)
            )

            with pytest.raises(workers_service.ClientRequestError):
                await workers_service.do_move(fen="fen", move="move", states={})

    @pytest.mark.parametrize(
        "response_content",
        [
            {"content": json.dumps({"message": "Internal Server Error"}).encode()},
        ],
    )
    @pytest.mark.asyncio
    async def test_do_move_server_request_exception(self, response_content):
        with respx.mock:
            respx.post(CONFIG.workers_url).mock(
                return_value=httpx.Response(500, **response_content)
            )

            with pytest.raises(workers_service.ServerRequestError):
                await workers_service.do_move(fen="fen", move="move", states={})
