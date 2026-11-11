---
name: fpsot-observability
description: Logging, tracing and metrics rules for FPSOT software. Use when writing or reviewing code that emits log records, audit events, business events for process mining, spans or metrics; when designing a log inventory, a log pipeline or a log store; or when setting retention, legal hold, destruction, pseudonyms for process mining or tamper-evident checkpoints.
---

# FPSOT observability

Summary of the FPSOT observability specification. It adds no rules of its own.
The spec text in `spec/` wins on any difference. Each line cites its requirement ID.
Examples are in `examples/`: a JSON Lines audit record, three business events in OTLP/JSON and their OCEL 2.0 export.

Each line keeps the strength of its rule: "must" and "must not" are MUST and MUST NOT, "should" and "should not" are SHOULD and SHOULD NOT, "may" is MAY.

Parties: a component emits records; a log store receives, keeps and destroys them; an integrity service is a separate part of a deployment (a sidecar or collector stage) that builds the Merkle tree; the operator is the public body that runs them.
The FPSOT identity and access specification owns the list of identity and access events and their content; this spec owns how any audit event is recorded, kept and protected.

## Profiles and versions

- A component, log store or integrity service must state its profiles in its inventory (OBS-010 or OBS-015) and meet every MUST of each; every component and log store must claim `base`; a component that serves or sends HTTP requests or remote procedure calls must claim `traces-metrics`; a component that emits business events must claim `process-mining` (OBS-001).
- A deployment that keeps an audit or business stream must protect it under `audit-integrity`; the log store may claim it, otherwise an integrity service must claim it, and a plain log store then claims only `base`; the deployment inventory must name the part that claims it (OBS-001).
- Follow the pinned versions: OpenTelemetry spec 1.62.0, opentelemetry-proto 1.11.1, semantic conventions 1.45.0 (Stable parts), W3C Trace Context Level 1, OCEL 2.0, C2SP tlog-checkpoint v1.1.0; a later minor version may be used if the parts used keep their status and meaning (OBS-002).
- Must not rely on OpenTelemetry features in Development or Alpha to meet a rule; may use them otherwise, and must then list them with their pinned version in the inventory (OBS-003).
- A conformance suite must check output only, never need source code (OBS-004).

## Inventory

- Each component must ship a machine-readable log inventory (JSON or YAML with a published JSON Schema) in its repository and with each release: profiles, event names with stream and default severity, attributes with types, destinations, retention class per stream, reader roles, concept schemes and versions, Development or Alpha features (OBS-010).
- Each attribute must have a personal information class (`none`, `pseudonymous`, `personal`, `sensitive`); a class other than `none` must state its purpose (OBS-011).
- Records must go only to destinations listed in the inventory (OBS-012).
- The operator should review the recorded events at each major version and at a set interval (OBS-013).
- Each event must belong to one stream, `technical`, `audit` or `business`; audit and business events must carry `org.fpsot.stream`; technical records may omit it (OBS-014).
- Each log store must ship an inventory, and each deployment must have one: profiles per part and who claims `audit-integrity`, streams kept and their senders, retention profile and period per stream, reader roles, checkpoint interval and origin, every log public key with its validity period (OBS-015).

## Records, names and time

- Records must follow the OpenTelemetry logs data model 1.62.0; an event is a record with a non-empty `EventName`; must not depend on a separate events API; `Body` should be a short fixed English text (OBS-020).
- Audit and business events must have an `EventName` of the form of NAM-050 and NAM-051, with no varying value and no label; technical records should have one (OBS-021).
- FPSOT attributes must start with `org.fpsot.`, follow the semantic conventions naming rules (dotted snake_case, an exception to NAM-010's lowerCamelCase) and NAM-004, NAM-005, NAM-006, NAM-009, and must not reuse a semconv namespace such as `process.`; semconv attributes keep their names (OBS-022).
- Each record must carry `service.name`, `service.namespace`, `service.version`, `service.instance.id` and `deployment.environment.name`; `service.instance.id` should be a random UUID and must not name a person or a personal device (OBS-023).
- Audit and business events must carry `org.fpsot.event.id`, a new identifier per DAT-063 and DAT-065, kept through every copy and export; technical records should (OBS-024).
- `SeverityNumber` must be 1 to 24 in the data model ranges; `SeverityText` should keep the source level (OBS-025).
- Must not emit `enduser.*` or the `event.name` attribute; must not record exceptions as span events; must record them as log records with `exception.type`, `exception.message` and `exception.stacktrace`; the inventory must class message and stacktrace as `personal` unless the component scrubs them (OBS-026).
- Each audit event must establish type, time, place, source, outcome and identities with `EventName`, `Timestamp`, resource attributes, `org.fpsot.actor.id`, `org.fpsot.actor.type` (`person`, `service`, `system`), `org.fpsot.actor.role`, `org.fpsot.network.client.prefix`, `org.fpsot.outcome` (`success`, `failure`), `error.type` and `org.fpsot.objects`; an event catalog of another FPSOT spec must name added attributes `org.fpsot.<domain>.<field>`, such as `org.fpsot.identity.session.id`; its JSON Schema governs the CloudEvents `data`, not the attributes (OBS-027).
- Must encode outside values so they cannot add a line, field or record; control characters must be escaped; must not build records from untrusted format strings (OBS-028).
- Must not exceed the record size limit of the inventory; should truncate long values and set `org.fpsot.truncated` (OBS-029).
- Text encodings must write instants per DAT-010, UTC with `Z`, at least milliseconds (OBS-030).
- OTLP must use integer nanoseconds, written in OTLP/JSON as a decimal string; DAT-013 does not apply inside OTLP; converters must convert to OBS-030 form without losing milliseconds (OBS-031).
- `Timestamp` must be the time of the event; readers must order events by `Timestamp`, never `ObservedTimestamp` (OBS-032).
- Each host must synchronize its clock with an authoritative source that the operator names, such as `time.nrc.ca`; should use Network Time Security when offered; the deployment guide must state the need (OBS-033).

## Audit events

- Must record each identity and access catalog event the component uses, under these rules, with both success and failure of each audit event; the log store or an integrity service protects it (OBS-040).
- Must record changes to configuration, security policy, logging policy and alert rules, naming the setting and actor, never a secret value (OBS-041).
- Must record each access to personal or sensitive information (read, create, change, delete, export, download, print); the privacy impact assessment scopes the reads recorded, and each access to Protected B or higher must be recorded as a floor (AU-02); each such event must carry a purpose code in `org.fpsot.purpose` from an operator scheme under VOC-001 and VOC-064 (OBS-042).
- A log store must record each read, query and export of its records and each change to a retention rule or legal hold (OBS-043).
- Must record security-control failures, bypass attempts, unexpected errors and crashes (OBS-044).
- Must record when logging starts, stops or cannot deliver; a log store must alert when an expected source is silent longer than the operator's period (OBS-045).
- Should map each audit event to an OCSF 1.9.0 class; a log store may then send OCSF to security tools (OBS-046).

## Traces

- Must read and send `traceparent` and `tracestate` (W3C Trace Context Level 1) on every HTTP request; a public-facing component may start a new trace; should set the Level 2 random flag when supported, and must not require it from others (OBS-050).
- Records inside a span must carry `TraceId`, `SpanId`, `TraceFlags`; in JSON Lines as lower-case hex `traceId` (32), `spanId` (16), `traceFlags` (2) (OBS-051).
- Must not put personal information, secrets or tokens in Baggage or `tracestate`; should not accept baggage from outside the trust boundary (OBS-052).
- Spans must use the Stable semantic conventions 1.45.0 for HTTP, database and remote calls; may add Development conventions under OBS-003; span names must not hold varying values; the component must drop or truncate `client.address`, `network.peer.address`, `url.query`, `url.full` and `user_agent.original` in its own process, before export (OBS-053).
- Span attributes must follow OBS-090 to OBS-092; must strip personal information and secrets from addresses and query strings, under API-085 (OBS-054).

## Metrics

- HTTP clients and servers must export the Stable HTTP duration metrics, and RPC callers the Stable call duration metrics, of semantic conventions 1.45.0 (OBS-060).
- Components and log stores must export pipeline health per stream (written, dropped, failed exports, last good export); hosts should export clock offset (OBS-061).
- Metric attributes must not hold person or business object identifiers or any unbounded value; this and OBS-090 also apply to exemplars and their filtered attributes (OBS-062).
- Should export metrics over OTLP; may also expose another open format (OBS-063).

## Business events

- Must emit an explicit business event at each boundary of each listed step, with `EventName` `org.fpsot.observability.activity.transitioned` and `org.fpsot.stream` = `business`; tools must not infer them from spans or database changes (OBS-070).
- Must carry `org.fpsot.activity.key`, a code (VOC-005, VOC-006, VOC-064) from an activity scheme of the vocabularies spec, never a label; one code must stand for one step, whatever its state (OBS-071).
- Must carry `org.fpsot.lifecycle`: `schedule`, `start`, `suspend`, `resume`, `complete`, `abort`; an instant step must emit only `complete`; a step with duration must emit `start` then `complete` or `abort`, with the same key and objects (OBS-072).
- Must carry `org.fpsot.objects`, a list of maps `{type, id, qualifier}`: a class of the data models spec or of the product's LinkML schema, named in the inventory (DMO-020); an internal string id (DAT-060, DAT-061; DAT-065 form for a UUID); a kebab-case qualifier; a log store may use flat `org.fpsot.object.<type>.<qualifier>.ids` attributes with type and qualifier in snake_case (`PartyRole` to `party_role`, `-` to `_`, reversible under NAM-011); converters must lose no reference (OBS-073).
- Must not use a trace or span identifier as a case or object identifier (OBS-074).
- Should carry `org.fpsot.performer.role` with the code of the role or unit; may add a `performer` object reference to a real person only if the privacy impact assessment allows, by an OBS-092 identifier; a `performer` reference must not point to a role or unit (OBS-075).
- Should carry `org.fpsot.bpmn.process.id`, `org.fpsot.bpmn.process.version`, `org.fpsot.bpmn.element.id` when a BPMN model exists; model versions must stay unchanged and reachable (OBS-076).
- Keys, qualifiers and event names must not hold free text, personal information or per-case values (OBS-077).
- Must not change or delete business events before retention ends; corrections must be new events with `org.fpsot.event.corrected_event.id` (OBS-078).
- The inventory should name the main case object type of each process (OBS-079).

## Export and transport

- Must write each record as one JSON object per line on standard output (DAT-001, DAT-003), with `timestamp`, `observedTimestamp`, `severityNumber`, `severityText`, `eventName`, `body`, `traceId`, `spanId`, `traceFlags`, `resource`, `attributes` (OBS-080).
- Should also export over OTLP (opentelemetry-proto 1.11.1, HTTP or gRPC); an informative note plans a MUST once the reference Java framework makes OpenTelemetry logs generally available, in a version that VCS-106 allows for a stricter rule (OBS-081).
- Audit and business records must reach a log store on another system, over TLS 1.2 or 1.3 with authenticated senders; must not keep the only copy locally longer than delivery takes (OBS-082).
- Must remove or mask personal information and secrets before a record leaves the process; a collector may filter again; rules must not rely on Alpha collector components (OBS-083).
- A log store should accept syslog (RFC 5424) and map it; may export CEF for a security tool, never as the only format (OBS-084).
- Inter-service business events should be CloudEvents under API-100 with the distributed tracing extension, and `id` should equal `org.fpsot.event.id` (OBS-085).
- Process-mining exports must be OCEL 2.0 JSON valid against the schema, one OCEL event per business event, mapped as the OBS-086 table shows (lifecycle and `performer-role` as event attributes); should also offer SQLite (OBS-086).
- Exports must replace identifiers that lead to a person with OBS-093 pseudonyms before leaving the log store; a raw internal ID of such an object must not appear (OBS-087).

## Privacy

- Must write personal information only in attributes declared for it; the operator must turn off those the privacy impact assessment does not name; `Body` and names of events, spans and metrics must not hold personal information (OBS-090).
- Must not hold passwords, secrets, keys, tokens, session cookies, authorization headers or full personal payloads; must keep only the network prefix (/24 IPv4, /48 IPv6) in `org.fpsot.network.client.prefix`; an event that the identity and access spec marks as needing the full client address may keep it in `client.address` when the assessment names it (OBS-091).
- Must name people by opaque internal identifiers (DAT-061, DAT-062), never by name, email or another body's identifier; display tools may look up names (OBS-092).
- Process-mining exports must use keyed pseudonyms (such as HMAC-SHA-256) per purpose and period, keeping at least 128 bits of output, with the key held and destroyed by a custodian outside the analysts; must not use unkeyed hashes (OBS-093).
- Documentation must state that pseudonymous records stay personal information, and must not call an export anonymous without the legal anonymization process (OBS-094).
- Access events must keep the purpose code apart from the actor; a log store should find all audit events of one object (OBS-095).
- Test, demo and training environments must use synthetic data only (TST-050), and their records must not reach production log stores (OBS-096).

## Retention, legal hold, destruction

- A log store must let the operator set retention per stream, online and storage tiers; must not hard-code periods; must not destroy before the period ends; the inventory (OBS-015) must state each stream's period (OBS-100).
- Must ship and apply by default `ca-qc-floor` to the audit and business streams: 90 days online then 180 days storage (FPSOT's additive reading of AU-11), 2 years for incident records; the operator must set longer where law or schedule asks; may ship other profiles; the technical stream period is set in the inventory and should stay short (OBS-101).
- Each retention rule must name the retention schedule rule it applies, recorded with each destruction (OBS-102).
- Must support a legal hold by object, time range or stream that stops destruction until lifted; each hold and lift must create an audit event (OBS-103).
- Each destruction run must create `org.fpsot.observability.record-batch.destroyed` with stream, range, count, rule and latest checkpoint, never the content (OBS-104).
- A move to another format or medium must keep a transfer record with method, date, count and hashes before and after (OBS-105).
- Each process-mining export must state purpose, retention and key end date beforehand; the custodian must destroy the key then (OBS-106).

## Integrity (audit-integrity profile)

These rules bind the log store, or the integrity service that claims the profile in its place (OBS-001). The Québec controls AU-09 and its parts are not mandatory; these are FPSOT's own choice.

- Must add each audit and business record to an append-only RFC 6962 Merkle tree; may add technical records; must keep each leaf hash (or tile) for the life of the tree (OBS-110).
- Each leaf must commit to SHA-256 over a random salt of 32 bytes or more and the UTF-8 JCS (RFC 8785) form of the JSON Lines record as stored, after any collector filter, with integers beyond 2^53 as strings; must keep the salt with the record and destroy both together (OBS-111).
- Must sign checkpoints in C2SP tlog-checkpoint v1.1.0 (`c2sp.org/tlog-checkpoint@v1.1.0`) with an Ed25519 log signature, at the OBS-015 inventory interval, should be at least hourly; the origin must name the log store and operator, and should be `<operator domain>/<log name>` (OBS-112).
- Must publish checkpoints to a separate store under another role, keep the private key per SEC-020 and SEC-023, and publish every public key the log has used with its validity period (OBS-113).
- At least one independent witness should cosign each checkpoint; a witness should use ML-DSA-44 cosignatures, as the format recommends; the log store may add its own ML-DSA-44 cosignature (OBS-114).
- Must check inclusion proofs on read, consistency of each new checkpoint, and the whole tree on schedule, recomputing the root from the kept leaf hashes and the leaf of each record still present; failures must alert and create an audit event (OBS-115).
- Should move closed tree segments and records to write-once storage; locks and backups must end by the destruction date unless a legal hold applies (OBS-116).
- Only a small privileged set may manage a log store, others must have read access only; an audited role must not be able to change its own records; should map integrity fields to OCSF `record_integrity` (OBS-117).
