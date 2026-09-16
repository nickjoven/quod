# Model admissions (LOCAL.md L1)

A model enters the tier L ladder only after a recorded decision by the owner and a registry
entry (`models/<name>.json`) that names its weights by sha256 and CID with the license read from
the model card at registration. Prose here is the decision; the JSON is the evidence.

| date | model | source | license (card) | base | decision |
|---|---|---|---|---|---|
| 2026-09-15 | Goedel-Prover-V2-8B | Goedel-LM/Goedel-Prover-V2-8B @ dfd02e6271a58375dfbf3ece0175277cf6b6a89a | apache-2.0 | Qwen/Qwen3-8B | **admitted** (Nick). Official safetensors converted and quantized here from that commit; no third-party GGUF. |
| 2026-09-15 | DeepSeek-Prover-V2-7B | DeepSeek-AI (MIT per card, to verify) | — | — | candidate, not admitted |
| 2026-09-15 | Kimina-Prover-Distill-8B | Moonshot/Numina (card to read) | — | Qwen3 | candidate, not admitted |
| 2026-09-15 | Qwen3-8B | Qwen (Apache-2.0) | — | — | candidate as the general control, not admitted |

Data-protection note: the admitted model's training corpus is formal mathematics (Lean statements
and proofs, Mathlib, synthetic formalizations); inference here runs locally on this project's own
statements. No personal data is processed by the pipeline; no GDPR statement from the model's
authors is known or relied on.
