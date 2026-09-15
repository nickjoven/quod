# models/ — the local model registry (LOCAL.md L1)

One JSON record per admitted weight file: sha256, ket CID, source repo and revision, quantization, context length, license, registration time. Weights themselves live in `models/weights/` (gitignored). A tier L prover config cites the record (`attempt_b.py --weights models/<name>.json`). Admission is a decision: `models_register.py add` refuses to run without a `--license` value.
