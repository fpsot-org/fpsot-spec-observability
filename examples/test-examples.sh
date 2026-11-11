#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Tests the example check of examples/check-examples.py:
#   - the examples in this folder pass the check;
#   - each broken copy below fails it, with the expected message. A check that
#     accepts a broken file would hide every later error.
#
# Needs only Python 3 and its standard library. Environment: PYTHON (default
# python3).
set -u
here="$(cd "$(dirname "$0")" && pwd)"
python=${PYTHON:-python3}
fail=0
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

check() { $python -I "$here/check-examples.py" "$1"; }

if ! out=$(check "$here"); then
  echo "FAIL: the examples do not pass the check:"; echo "$out"; fail=1
fi

# broken NAME FILE PYTHON-EXPRESSION EXPECTED-TEXT
# Copies the examples, rewrites FILE with the expression (applied to its text
# as the variable t), and expects the check to fail with EXPECTED-TEXT.
broken() {
  local name=$1 file=$2 expr=$3 want=$4 dir="$work/$1"
  mkdir -p "$dir"
  cp "$here"/log-record.jsonl "$here"/business-events.otlp.json "$here"/ocel-export.json "$dir"/
  $python -I -c "import sys,pathlib; p=pathlib.Path(sys.argv[1]); t=p.read_text(encoding='utf-8'); p.write_text($expr, encoding='utf-8')" "$dir/$file"
  if out=$(check "$dir"); then
    echo "FAIL: the check accepted the broken copy $name"; fail=1; return
  fi
  if ! grep -qF -- "$want" <<<"$out"; then
    echo "FAIL: the check rejected $name, but not for the expected reason: $want"; echo "$out"; fail=1
  fi
}

broken full-ip log-record.jsonl "t.replace('192.0.2.0/24', '192.0.2.17')" "full IP address"
broken no-event-id log-record.jsonl "t.replace('org.fpsot.event.id', 'org.fpsot.event.ref')" "org.fpsot.event.id"
broken local-time log-record.jsonl "t.replace('Z\"', '-05:00\"', 1)" "RFC 3339 in UTC"
broken deprecated-attribute log-record.jsonl "t.replace('org.fpsot.outcome', 'enduser.id', 1)" "forbidden attribute enduser.id"
broken bad-lifecycle business-events.otlp.json "t.replace('\"start\"', '\"started\"', 1)" "org.fpsot.lifecycle"
broken trace-as-case business-events.otlp.json "t.replace('01a1c5c4-db10-7a3f-8c41-2d9e6f0a1b23', '4bf92f3577b34da6a3ce929d0e0e4736')" "trace ID must not serve"
broken ocel-wrong-type ocel-export.json "t.replace('\"type\": \"review-application\"', '\"type\": \"Review application\"', 1)" "is not declared"
broken ocel-missing-event ocel-export.json "__import__('json').dumps(dict(__import__('json').loads(t), events=__import__('json').loads(t)['events'][1:]))" "no event with the ID"
broken ocel-raw-id ocel-export.json "t.replace('ps-7c1e9a4f20b85d36e1a04b9c2f6d8e3a', '01a1c5c4-db10-7a3f-8c41-2d9e6f0a1b23')" "not pseudonymized"
broken body-name-sin log-record.jsonl "t.replace('Application file exported', 'Application file of Firstname Lastname, SIN 123 456 782, exported')" "social insurance number"
broken url-query log-record.jsonl "t.replace('\"org.fpsot.export.format\"', '\"url.full\":\"https://permits.example.org/files/42?token=abc123&email=firstname.lastname@example.org\",\"org.fpsot.export.format\"')" "url.full must not hold a query"

[ $fail -eq 0 ] && echo "PASS"
exit $fail
