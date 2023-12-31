# Chessticulate API
REST API for our chessticulate website.

## Setup
1. Clone repository: `git clone git@github.com:chessticulate/chessticulate-api && cd chessticulate-api`
2. Create virtual environment: `python -m venv venv && source venv/bin/activate`
3. Editable install: `pip install -e .[dev]`

## Development tools
- Run formatters: `black . && isort .`
- Run linter: `pylint app`
- Run tests: `pytest`

## CI
Whenever you push up a new branch, the github workflows located under `./.github/workflows/` will be triggered. These workflows as of now check for the following:
- the code has been formatted properly according to `black` and `isort`.
- there are no linter errors.
- all the tests pass.
- the version number located in pyproject.toml is greater than the one in the main branch.

Be sure to run the commands under "Development tools" before pushing up changes. Or at least if you want to be able to merge. If any of these checks are failing, you will not be able to merge with main.

## Deployment
TODO
