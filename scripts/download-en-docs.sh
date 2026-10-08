#!/usr/bin/env bash
# Download all TypeSafe docs (Markdown) from docs.typesafe.ai into documentation/en/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/documentation/en"
BASE="https://docs.typesafe.ai"
INDEX_URL="${BASE}/llms.txt"
ERROR_LOG="${OUT}/_download-errors.log"
TMP_URLS="$(mktemp)"

mkdir -p "${OUT}"
: > "${ERROR_LOG}"

echo "Fetching index: ${INDEX_URL}"
curl -fsSL "${INDEX_URL}" -o "${OUT}/llms.txt"

# Extract unique page paths from .md links
rg -o 'https://docs\.typesafe\.ai/[^)\s]+\.md' "${OUT}/llms.txt" \
  | sed "s|${BASE}/||; s|\.md$||" \
  | sort -u > "${TMP_URLS}"

TOTAL="$(wc -l < "${TMP_URLS}" | tr -d ' ')"
echo "Found ${TOTAL} pages. Downloading to ${OUT}/"

ok=0
fail=0
i=0

while IFS= read -r path; do
  i=$((i + 1))
  dest="${OUT}/${path}.md"
  mkdir -p "$(dirname "${dest}")"
  url="${BASE}/${path}.md"
  printf '[%d/%d] %s\n' "${i}" "${TOTAL}" "${path}"

  if curl -fsSL --retry 2 --retry-delay 1 "${url}" -o "${dest}"; then
    # Reject empty or HTML error pages masquerading as markdown
    if [[ ! -s "${dest}" ]] || head -c 20 "${dest}" | grep -qi '<!DOCTYPE\|<html'; then
      echo "${path}" >> "${ERROR_LOG}"
      fail=$((fail + 1))
      rm -f "${dest}"
    else
      ok=$((ok + 1))
    fi
  else
    echo "${path}" >> "${ERROR_LOG}"
    fail=$((fail + 1))
    rm -f "${dest}"
  fi
done < "${TMP_URLS}"

# One retry pass for failures
if [[ -s "${ERROR_LOG}" ]]; then
  echo "Retrying failed pages..."
  RETRY_LIST="$(mktemp)"
  cp "${ERROR_LOG}" "${RETRY_LIST}"
  : > "${ERROR_LOG}"
  while IFS= read -r path; do
    [[ -z "${path}" ]] && continue
    dest="${OUT}/${path}.md"
    mkdir -p "$(dirname "${dest}")"
    url="${BASE}/${path}.md"
    echo "retry: ${path}"
    if curl -fsSL --retry 3 --retry-delay 2 "${url}" -o "${dest}" \
      && [[ -s "${dest}" ]] \
      && ! head -c 20 "${dest}" | grep -qi '<!DOCTYPE\|<html'; then
      ok=$((ok + 1))
      fail=$((fail - 1))
    else
      echo "${path}" >> "${ERROR_LOG}"
      rm -f "${dest}"
    fi
  done < "${RETRY_LIST}"
  rm -f "${RETRY_LIST}"
fi

rm -f "${TMP_URLS}"

echo "Done. ok=${ok} fail=${fail} total=${TOTAL}"
if [[ -s "${ERROR_LOG}" ]]; then
  echo "Failures listed in ${ERROR_LOG}"
  exit 1
else
  rm -f "${ERROR_LOG}"
fi
