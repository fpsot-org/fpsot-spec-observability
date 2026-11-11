# Instructions for agents

This repository holds the FPSOT observability specification: the log inventory, the record model on OpenTelemetry, names, identifiers and timestamps, audit events, trace propagation, metrics, business events for process mining and their OCEL 2.0 export, transport, privacy and pseudonyms, retention, legal hold and destruction, and tamper evidence with Merkle trees and C2SP checkpoints.

- The normative text is in `spec/en/` and `spec/fr/`. Every rule has an ID such as `OBS-001`.
- Follow `skill/SKILL.md` when you write or review code that emits logs, audit events, business events, spans or metrics, or that stores or destroys them. The spec text wins on any difference.
- Every page exists in English and in French, with the same file name and the same IDs.
- Terms and abbreviations come from the term base of `fpsot-spec-writing`. Add a missing term there first; `TERMS-NEEDED.md` lists the ones this spec waits for.
- This is a layer 1 specification. It may refer to the layer 0 specifications, to data types, vocabularies, data models, api-restful, testing and security. It refers to the identity and access specification by topic only. It never refers to the registry, code or capability specifications, except by topic.
- The identity and access specification lists the identity and access events and their content. This specification sets how any audit event is recorded, kept and protected. Do not add identity events here.
- Do not name a product in a rule. Name the standard or the capability; products may appear only on the informative page `implementation.adoc`.
- Examples and fixtures hold synthetic data only: no real names, documentation addresses from RFC 5737, and network prefixes instead of full client addresses. Run `bash examples/test-examples.sh` after changing an example.
- Do not copy text from OpenTelemetry, OWASP, NIST, W3C, C2SP, the CGCD or any government. Summarize in your own words and cite the exact version.
- Do not state a legal point as a rule. Points that need a lawyer go in an informative note or in `counsel.adoc`, and an article number that nobody checked is marked "to be verified".
- Commits follow Conventional Commits and are signed. Pull requests are squash-merged.
