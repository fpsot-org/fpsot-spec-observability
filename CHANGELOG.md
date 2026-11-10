# Changelog

All notable changes to this specification are listed here.
The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-10

### Added

- Scope, parties, streams and profiles OBS-001 to OBS-004: the `base`, `traces-metrics`, `process-mining` and `audit-integrity` profiles, pinned versions of OpenTelemetry 1.62.0, opentelemetry-proto 1.11.1, semantic conventions 1.45.0, W3C Trace Context Level 1, OCEL 2.0 and C2SP tlog-checkpoint v1.1.0, no reliance on Development or Alpha features, and conformance suites that check output only.
- Log inventory rules OBS-010 to OBS-014: a machine-readable inventory per component, a personal information class and a purpose for each attribute, listed destinations, review of events, and the technical, audit and business streams.
- Record rules OBS-020 to OBS-033: the OpenTelemetry logs data model, event names under NAM-050, attributes under `org.fpsot.`, the stable resource attributes, `org.fpsot.event.id`, severity, no deprecated attributes, the content of audit events, encoding against log injection, a size limit, UTC timestamps with milliseconds in text and nanoseconds in OTLP, occurrence time, and clocks synchronized with an authoritative source.
- Audit event rules OBS-040 to OBS-046: the identity and access catalog of the FPSOT identity and access specification, configuration and alert-rule changes, access to personal information with a purpose code, access to the logs, security-control failures, logging stops, and an OCSF 1.9.0 mapping as a recommendation.
- Trace rules OBS-050 to OBS-054 and metrics rules OBS-060 to OBS-063.
- Business event rules OBS-070 to OBS-079: one event name, activity keys from a vocabulary scheme, a lifecycle code, a list of typed object references with flattened keys as a fallback, no trace identifier as a case, performers as roles, BPMN references, append-only corrections and a main case per process.
- Export and transport rules OBS-080 to OBS-087: JSON Lines on the standard output, OTLP as a recommendation that becomes a requirement once the reference framework makes OpenTelemetry logs generally available, a separate log store over TLS, masking at the source, syslog and CEF, CloudEvents between services, and the OCEL 2.0 export with pseudonyms.
- Privacy rules OBS-090 to OBS-096, retention rules OBS-100 to OBS-106 with the default profile `ca-qc-floor` (90 days online, 180 days in storage, 2 years for incidents), legal hold and destruction records, and integrity rules OBS-110 to OBS-117 with a Merkle tree over salted hashes, Ed25519 checkpoints, witnesses and write-once storage.
- Informative pages on implementation profiles and questions for counsel.
- Examples: a JSON Lines audit record, three business events in OTLP/JSON and their OCEL 2.0 export, with a check script and its test, run by the `examples` job of the continuous integration.
- Comparison data with Canada and Québec rows.
- How-to guide that makes a component observable.

[Unreleased]: https://github.com/fpsot-org/fpsot-spec-observability/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fpsot-org/fpsot-spec-observability/releases/tag/v0.1.0
