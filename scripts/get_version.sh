#!/usr/bin/bash

VERSION=$(grep '^version = "[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+"' pyproject.toml | cut -d '"' -f 2)

echo "$VERSION"

