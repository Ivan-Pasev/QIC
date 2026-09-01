# QIC Roadmap

QIC progresses through evidence-gated implementation slices. Architectural scope does not count as implementation closure.

## Phase A — Genesis kernel

### QIC-G0 — Repository + constitutional spine

Deliver:
- public project/governance documentation;
- package/test/CI skeleton;
- constitutional schema directory;
- explicit claim boundary and state handoff.

### QIC-G1 — Canonical serializer + digest kernel

Deliver deterministic canonical serialization and stable content digests with golden vectors.

### QIC-G2 — Root ontology + maturity vector

Implement root ontology classes, typed IDs, transition families, and maturity/evidence classes.

### QIC-G3 — Authority + capability model

Implement scoped authority grants, capability closure, non-amplification checks, and authority test cases.

### QIC-G4 — Transition engine + invariant gate

Implement propose/validate/authorize/execute/verify/commit/witness transaction flow.

### QIC-G5 — Chrono + witness

Implement append-only causal events, transaction witnesses, and replay/recovery semantics.

### QIC-G6 — Minimal KBI

Implement a minimal claim/evidence/provenance lifecycle with explicit epistemic transitions.

### QIC-G7 — Genesis CLI + verification

Expose repository/init/status/manifest/registry/witness/implementation verification commands.

### QIC-G8 — Adversarial constitutional tests

Add fault injection, property tests, mutation tests, illegal-transition cases, and recovery qualification.

**Phase A exit:** credible executable `I00` closure.

## Phase B — Knowledge and cognitive fabric

- `I01` provenance-rich KBI plus Holo/Topo/Knot derived processors.
- `I02` bounded MLCO compiler, Hermes missions, Omnius scheduling.
- `I03` executable state model and formal/runtime conformance subset.
- `I04` adversarial qualification and failure atlas.
- `I05` performance observatory and accelerator-candidate evidence.

## Phase C — Sovereign distributed science

- `I06` FQNP three-node sovereign federation.
- `I07` Federated Knowledge Contracts and distributed scientific closure.

## Phase D — Physical reference systems

- `I08` low-consequence laboratory measurement and CPTG.
- `I09` multi-cell/polyplant resource coordination preserving local safety.
- `I10` bounded online identification/adaptation with shadow validation and rollback.
- `I11` engineering digital thread, commissioning, and successor physical baselines.

## Release discipline

Every release must identify:

- implemented scope;
- test/qualification evidence;
- formal-model scope if present;
- simulation/hardware status;
- known limitations;
- unresolved claims;
- witness/manifest roots where implemented.

The roadmap may change through ADRs and versioned governance decisions. Maturity labels may only move upward when evidence supports the change.
