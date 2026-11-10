# Jurisdictions

Comparison data per jurisdiction.
The format is defined by the FPSOT documentation specification (fpsot-spec-doc), in `model/jurisdiction.yaml`.

- `baseline.yaml` lists the topics, and one row per compared requirement with its international baseline and FPSOT default.
- `<cc>.yaml` holds one country, such as `ca.yaml`. `<cc>/<sub>.yaml` holds one subdivision, such as `ca/qc.yaml`.

The continuous integration writes the comparison pages under `docs/modules/<lang>/pages/jurisdictions/`.
Do not edit those pages by hand.
