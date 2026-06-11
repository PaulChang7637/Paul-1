#!/usr/bin/env bash
# Install Ollama (if needed) and start the server, then print its status.
#
# Installs from GitHub releases instead of ollama.com, so it works in
# sandboxes whose network policy allows github.com but not ollama.com
# (e.g. Claude Code cloud environments). Requires root for the install
# step (writes to /usr/local, may apt-get install zstd).
#
# Usage: ./scripts/ollama-up.sh
#   OLLAMA_VERSION=v0.30.7  pin a release (default: latest)
#   OLLAMA_HOST=host:port   bind address (default: 127.0.0.1:11434)
set -euo pipefail

VERSION="${OLLAMA_VERSION:-}"
HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  if [ -z "$VERSION" ]; then
    VERSION=$(curl -fsSI https://github.com/ollama/ollama/releases/latest \
      | tr -d '\r' | sed -n 's#^[Ll]ocation: .*/tag/##p')
  fi
  case "$(uname -m)" in
    x86_64) ARCH=amd64 ;;
    aarch64 | arm64) ARCH=arm64 ;;
    *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;;
  esac
  ASSET="ollama-linux-${ARCH}.tar.zst"
  BASE="https://github.com/ollama/ollama/releases/download/${VERSION}"

  command -v zstd >/dev/null 2>&1 || apt-get install -y -qq zstd

  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT
  echo "Downloading ollama ${VERSION} (${ASSET})..."
  curl -fSL --retry 3 -o "${TMP}/${ASSET}" "${BASE}/${ASSET}"
  curl -fsSL -o "${TMP}/sha256sum.txt" "${BASE}/sha256sum.txt"
  (cd "$TMP" && grep " ${ASSET}\$" sha256sum.txt | sha256sum -c -)
  tar --zstd -xf "${TMP}/${ASSET}" -C /usr/local
fi

if ! curl -fsS --max-time 2 "http://${HOST}/api/version" >/dev/null 2>&1; then
  echo "Starting ollama serve on ${HOST}..."
  OLLAMA_HOST="$HOST" nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  for _ in $(seq 1 30); do
    curl -fsS --max-time 1 "http://${HOST}/api/version" >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo -n "Connected: "
curl -fsS "http://${HOST}/api/version"
echo
OLLAMA_HOST="$HOST" ollama list
