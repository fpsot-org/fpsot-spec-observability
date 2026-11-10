#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Checks the example files of the FPSOT observability specification.

Usage: check-examples.py DIR

DIR holds three files:
  - log-record.jsonl: JSON Lines log records (OBS-020 to OBS-031, OBS-080);
  - business-events.otlp.json: an OTLP/JSON request with business events
    (OBS-070 to OBS-076);
  - ocel-export.json: the OCEL 2.0 export of those events (OBS-086, OBS-087).

The check uses the Python standard library only. It fails when a file does
not parse, when a required field is missing or has the wrong form, when a
record holds a forbidden attribute or a full IP address (OBS-091), or when the
OCEL export does not match the business events it comes from.
"""
import datetime
import json
import pathlib
import re
import sys

UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,9}Z$")
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
EVENT_NAME = re.compile(r"^org\.fpsot(\.[a-z][a-z0-9]*(-[a-z0-9]+)*){3}$")
HEX32 = re.compile(r"^[0-9a-f]{32}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
FULL_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?!/)")
LINKML_CLASS = re.compile(r"^[A-Z][A-Za-z0-9]*$")

RESOURCE_KEYS = ("service.name", "service.namespace", "service.version",
                 "service.instance.id", "deployment.environment.name")
FORBIDDEN_PREFIXES = ("enduser.", "process.")
FORBIDDEN_KEYS = ("event.name", "user.name", "user.full_name", "user.email",
                  "password", "token", "authorization")
OUTCOMES = ("success", "failure")
LIFECYCLE = ("schedule", "start", "suspend", "resume", "complete", "abort")
BUSINESS_EVENT = "org.fpsot.observability.activity.transitioned"

errors = []


def fail(where, message):
    errors.append(f"{where}: {message}")


def check_keys(where, keys):
    for key in keys:
        if key.startswith(FORBIDDEN_PREFIXES) or key in FORBIDDEN_KEYS:
            fail(where, f"forbidden attribute {key} (OBS-022, OBS-026, OBS-091)")


def check_no_full_ip(where, value):
    text = json.dumps(value)
    for match in FULL_IPV4.finditer(text):
        fail(where, f"full IP address {match.group()} (OBS-091)")


def check_json_lines(path):
    lines = [l for l in path.read_text(encoding="utf-8").split("\n") if l.strip()]
    if not lines:
        fail(path.name, "no record")
    for n, line in enumerate(lines, 1):
        where = f"{path.name}:{n}"
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            fail(where, f"not JSON: {e}")
            continue
        if not isinstance(rec, dict):
            fail(where, "a record must be a JSON object")
            continue
        for key in ("timestamp", "observedTimestamp", "severityNumber", "severityText",
                    "eventName", "resource", "attributes"):
            if key not in rec:
                fail(where, f"missing {key}")
        for key in ("timestamp", "observedTimestamp"):
            if key in rec and not INSTANT.match(str(rec[key])):
                fail(where, f"{key} must be RFC 3339 in UTC with milliseconds (OBS-030)")
        sev = rec.get("severityNumber")
        if not isinstance(sev, int) or not 1 <= sev <= 24:
            fail(where, "severityNumber must be an integer from 1 to 24 (OBS-025)")
        if not EVENT_NAME.match(str(rec.get("eventName", ""))):
            fail(where, "eventName must have the form org.fpsot.<domain>.<resource>.<event> (OBS-021)")
        resource = rec.get("resource", {})
        for key in RESOURCE_KEYS:
            if not resource.get(key):
                fail(where, f"resource lacks {key} (OBS-023)")
        attrs = rec.get("attributes", {})
        check_keys(where, list(resource) + list(attrs))
        if not UUID7.match(str(attrs.get("org.fpsot.event.id", ""))):
            fail(where, "org.fpsot.event.id must be a lower-case version 7 UUID (OBS-024)")
        if attrs.get("org.fpsot.outcome") not in OUTCOMES:
            fail(where, "org.fpsot.outcome must be success or failure (OBS-027)")
        if "traceId" in rec and not HEX32.match(rec["traceId"]):
            fail(where, "traceId must be 32 lower-case hex digits (OBS-051)")
        if "spanId" in rec and not HEX16.match(rec["spanId"]):
            fail(where, "spanId must be 16 lower-case hex digits (OBS-051)")
        check_no_full_ip(where, rec)


def any_value(v):
    """Turns an OTLP/JSON AnyValue into a plain Python value."""
    if not isinstance(v, dict) or len(v) != 1:
        raise ValueError(f"not an AnyValue: {v!r}")
    (kind, inner), = v.items()
    if kind == "stringValue":
        return inner
    if kind == "intValue":
        return int(inner)
    if kind == "boolValue":
        return bool(inner)
    if kind == "doubleValue":
        return float(inner)
    if kind == "arrayValue":
        return [any_value(x) for x in inner.get("values", [])]
    if kind == "kvlistValue":
        return {kv["key"]: any_value(kv["value"]) for kv in inner.get("values", [])}
    raise ValueError(f"unknown AnyValue kind {kind}")


def attributes(where, items):
    out = {}
    for kv in items or []:
        try:
            out[kv["key"]] = any_value(kv["value"])
        except (KeyError, ValueError) as e:
            fail(where, f"bad attribute: {e}")
    return out


def nanos_to_instant(nanos):
    seconds, rest = divmod(int(nanos), 1_000_000_000)
    t = datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S") + f".{rest // 1_000_000:03d}Z"


def check_business_events(path):
    """Returns the business events as plain dicts, for the OCEL check."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(path.name, f"not JSON: {e}")
        return []
    events = []
    for r, rl in enumerate(doc.get("resourceLogs", [])):
        resource = attributes(f"{path.name} resource {r}", rl.get("resource", {}).get("attributes"))
        for key in RESOURCE_KEYS:
            if not resource.get(key):
                fail(f"{path.name} resource {r}", f"lacks {key} (OBS-023)")
        for sl in rl.get("scopeLogs", []):
            for n, lr in enumerate(sl.get("logRecords", [])):
                where = f"{path.name} record {n}"
                if lr.get("eventName") != BUSINESS_EVENT:
                    fail(where, f"eventName must be {BUSINESS_EVENT} (OBS-070)")
                nanos = str(lr.get("timeUnixNano", ""))
                if not nanos.isdigit():
                    fail(where, "timeUnixNano must be integer nanoseconds (OBS-031)")
                    continue
                attrs = attributes(where, lr.get("attributes"))
                check_keys(where, list(resource) + list(attrs))
                check_no_full_ip(where, lr)
                event_id = attrs.get("org.fpsot.event.id", "")
                if not UUID7.match(str(event_id)):
                    fail(where, "org.fpsot.event.id must be a lower-case version 7 UUID (OBS-024)")
                key = attrs.get("org.fpsot.activity.key", "")
                if not KEBAB.match(str(key)):
                    fail(where, "org.fpsot.activity.key must be a kebab-case code (OBS-071)")
                if attrs.get("org.fpsot.lifecycle") not in LIFECYCLE:
                    fail(where, "org.fpsot.lifecycle must be a code of OBS-072")
                objects = attrs.get("org.fpsot.objects")
                if not isinstance(objects, list) or not objects:
                    fail(where, "org.fpsot.objects must be a non-empty list (OBS-073)")
                    objects = []
                for o in objects:
                    if not isinstance(o, dict) or set(o) != {"type", "id", "qualifier"}:
                        fail(where, f"object reference must hold type, id and qualifier only: {o!r}")
                        continue
                    if not LINKML_CLASS.match(o["type"]):
                        fail(where, f"object type {o['type']} must be a LinkML class name (OBS-073)")
                    if not KEBAB.match(o["qualifier"]):
                        fail(where, f"qualifier {o['qualifier']} must be kebab-case (OBS-073)")
                trace = lr.get("traceId", "")
                if trace and any(o.get("id") == trace for o in objects if isinstance(o, dict)):
                    fail(where, "the trace ID must not serve as a case or object ID (OBS-074)")
                events.append({"id": event_id, "type": key, "time": nanos_to_instant(nanos),
                               "lifecycle": attrs.get("org.fpsot.lifecycle"), "objects": objects})
    if not events:
        fail(path.name, "no business event")
    return events


def check_ocel(path, business):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(path.name, f"not JSON: {e}")
        return
    for key in ("eventTypes", "objectTypes", "events", "objects"):
        if not isinstance(doc.get(key), list):
            fail(path.name, f"missing the array {key} (OCEL 2.0 JSON schema)")
            return
    event_types = {t.get("name") for t in doc["eventTypes"]}
    object_types = {t.get("name") for t in doc["objectTypes"]}
    for t in doc["eventTypes"] + doc["objectTypes"]:
        if "name" not in t or not isinstance(t.get("attributes"), list):
            fail(path.name, f"a type needs name and attributes: {t!r}")
    objects = {}
    for o in doc["objects"]:
        if not {"id", "type"} <= set(o):
            fail(path.name, f"an object needs id and type: {o!r}")
            continue
        if o["type"] not in object_types:
            fail(path.name, f"object type {o['type']} is not declared")
        objects[o["id"]] = o
    by_id = {}
    for e in doc["events"]:
        if not {"id", "type", "time"} <= set(e):
            fail(path.name, f"an event needs id, type and time: {e!r}")
            continue
        if e["type"] not in event_types:
            fail(path.name, f"event type {e['type']} is not declared")
        if not INSTANT.match(e["time"]):
            fail(path.name, f"event time {e['time']} must be RFC 3339 in UTC (OBS-030)")
        for rel in e.get("relationships", []):
            if rel.get("objectId") not in objects:
                fail(path.name, f"event {e['id']} links to an unknown object {rel.get('objectId')}")
        by_id[e["id"]] = e
    check_no_full_ip(path.name, doc)
    if len(by_id) != len(business):
        fail(path.name, f"{len(by_id)} events, but {len(business)} business events")
    for b in business:
        e = by_id.get(b["id"])
        if e is None:
            fail(path.name, f"no event with the ID {b['id']} (OBS-086)")
            continue
        if e["type"] != b["type"]:
            fail(path.name, f"event {b['id']}: type {e['type']}, expected the activity key {b['type']}")
        if e["time"] != b["time"]:
            fail(path.name, f"event {b['id']}: time {e['time']}, expected {b['time']}")
        attrs = {a.get("name"): a.get("value") for a in e.get("attributes", [])}
        if attrs.get("lifecycle") != b["lifecycle"]:
            fail(path.name, f"event {b['id']}: the lifecycle attribute must be {b['lifecycle']}")
        rels = e.get("relationships", [])
        if sorted(r.get("qualifier") for r in rels) != sorted(o["qualifier"] for o in b["objects"]):
            fail(path.name, f"event {b['id']}: qualifiers differ from the business event (OBS-086)")
        for r in rels:
            o = objects.get(r.get("objectId"))
            want = [x["type"] for x in b["objects"] if x["qualifier"] == r.get("qualifier")]
            if o is not None and o["type"] not in want:
                fail(path.name, f"event {b['id']}: object {o['id']} has the type {o['type']}, expected {want}")


def main():
    if len(sys.argv) != 2:
        print("usage: check-examples.py DIR", file=sys.stderr)
        return 2
    here = pathlib.Path(sys.argv[1])
    files = {name: here / name for name in
             ("log-record.jsonl", "business-events.otlp.json", "ocel-export.json")}
    for name, path in files.items():
        if not path.is_file():
            fail(name, "file not found")
    if not errors:
        check_json_lines(files["log-record.jsonl"])
        business = check_business_events(files["business-events.otlp.json"])
        check_ocel(files["ocel-export.json"], business)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
