# QIC Architecture

## 1. Purpose

QIC is a sovereign cybernetic computing architecture organized around evidence-bearing state transitions, explicit authority boundaries, bounded processors, causal witnesses, and progressively qualified physical integration.

## 2. Constitutional planes

- **P0 Constitution** — invariant, authority, and transition law.
- **P1 Epistemic State** — authoritative KBI state.
- **P2 Cognitive Execution** — MLCO, Hermes, and derived reasoning.
- **P3 Orchestration** — Omnius scheduling and processor/resource coordination.
- **P4 Compute** — reference and heterogeneous processor backends.
- **P5 Temporal/Witness** — Chrono and witness hierarchy.
- **P6 Sovereign Federation** — FQNP remote exchange.
- **P7 Cyber-Physical** — measurement and bounded physical transitions.
- **P8 Evolution** — bounded adaptation and engineering change.

## 3. Root ontology

Seven root classes:

`STATE`, `ACTOR`, `OPERATION`, `CONSTRAINT`, `EVIDENCE`, `RESOURCE`, `WITNESS`.

Transition families:

- `T0` Observation
- `T1` Derivation
- `T2` Epistemic
- `T3` Computational
- `T4` Physical
- `T5` Evolutionary

Authority domains:

- `A_E` epistemic
- `A_C` computational
- `A_P` physical
- `A_X` evolutionary/engineering

Authority is scoped and non-transitive.

## 4. Trusted core

The trusted core should stay intentionally small:

1. canonical serializer;
2. state model;
3. invariant gate;
4. authority gate;
5. commit transition;
6. Chrono append;
7. witness construction;
8. later, the cyber-physical transition gate.

LLMs, derived processors, external services, accelerators, simulations, and remote nodes remain non-authoritative until their outputs cross an explicit admission/promotion boundary.

## 5. Primary processors

### KBI

The sole authoritative knowledge-state processor. It manages claims, evidence, provenance, contradiction, relations, and epistemic transition history.

### Holo

Derived semantic/projection processor. Produces candidate relations only.

### Topo

Graph/topology processor for connectivity, SCCs, reachability, cycles, bridges, articulation points, and dependency analysis.

### Knot

Structural pathology processor over Topo for circular evidence/provenance and other dependency traps.

### Hermes

Bounded planner/agent. It may inspect, plan, audit, and propose but does not receive default KBI mutation authority.

### MLCO

Bounded compilation/execution layer. It translates missions into registered, typed, capability-scoped operations. It is not intended to be an unrestricted shell language.

### Omnius

Scheduler/orchestrator over jobs, processors, retries, and resources. Omnius does not own epistemic authority.

### Chrono

Append-only causal genealogy over transitions, branches, epochs, state digests, and witness lineage.

## 6. Federation

FQNP defines typed sovereign exchange among QIC nodes.

Core laws:

`RemoteState != LocalAuthority`

`Receive != Admit`

`Signature != Truth`

Remote evidence, capsules, and reconciliation proposals remain namespaced until locally admitted.

## 7. Scientific closure

Federated Knowledge Contracts bind participants, roles, protocols, criteria, evidence independence, replication, local acceptance, and closure. Closure classes include full, qualified, negative, inconclusive, and contested outcomes without treating any as universal truth values.

## 8. Cyber-physical transition

Physical effects must pass through an explicit Cyber-Physical Transition Gate (CPTG). The chain is:

`proposal -> authorization -> one-shot permit -> bounded command -> acknowledgement -> consequence measurement -> witness`.

Raw acquisition remains immutable and measurement, calibration, processing, interpretation, and claim admission remain separate layers.

## 9. Multi-plant composition

Higher layers coordinate services and resources rather than writing raw local actuator values. Local CPTG and safety state remain authoritative over each physical cell.

## 10. Adaptation and engineering evolution

Model/controller candidates are non-authoritative until validated and promoted. Hard safety is not a learning surface. Physical architecture change is a separate engineering transition requiring explicit review, as-built capture, commissioning, and a new baseline.

## 11. Heterogeneous compute

Processor backends are accessed through stable interfaces and may eventually include CPU, GPU, FPGA, ASIC, photonic research, or QPU research backends. Accelerator selection is driven by measured bottlenecks, not branding or architecture speculation.

## 12. Implementation ladder

- `I00` constitutional repository genesis
- `I01` KBI/provenance/Holo-Topo-Knot
- `I02` MLCO/Hermes/Omnius
- `I03` executable-state/formal-runtime conformance
- `I04` adversarial qualification
- `I05` performance observatory
- `I06` FQNP federation
- `I07` federated scientific closure
- `I08` laboratory/CPTG
- `I09` polyplant coordination
- `I10` bounded adaptation
- `I11` engineering digital thread and physical evolution

The current public implementation begins with `QIC-G0` through `QIC-G8`, which together target a credible executable `I00` closure.
