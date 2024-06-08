"""Chessticulate API Entrypoint"""

import uvicorn

from chessticulate_api.config import CONFIG


def main():
    """run API with uvicorn"""
    uvicorn.run(
        "chessticulate_api:app", port=CONFIG.app_port, log_level=CONFIG.log_level
    )


if __name__ == "__main__":
    main()
