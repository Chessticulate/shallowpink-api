"""Chessticulate API Entrypoint"""

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from chessticulate_api.config import CONFIG


def main():
    """run API with uvicorn"""

    LOGGING_CONFIG["formatters"]["default"][
        "fmt"
    ] = "%(asctime)s %(levelprefix)s %(message)s"

    LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelprefix)s %(client_addr)s -"
        ' "%(request_line)s" %(status_code)s'
    )

    uvicorn.run(
        "chessticulate_api:app",
        host=CONFIG.app_host,
        port=CONFIG.app_port,
        log_level=CONFIG.log_level,
    )


if __name__ == "__main__":
    main()
