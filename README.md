# RUKH — AI-powered Smart Contract Audit & Test Synthesis

[![CI](https://github.com/VolodymyrStetsenko/rukh/actions/workflows/ci.yml/badge.svg)](https://github.com/VolodymyrStetsenko/rukh/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/VolodymyrStetsenko/rukh)](https://github.com/VolodymyrStetsenko/rukh/releases)

**By Volodymyr Stetsenko (Zero2Auditor)**

**Tagline:** Red-Team AI for Smart Contracts — think like black-hat, act white-hat.

---

## Overview

RUKH is a professional platform for auditors and Web3 teams that ingests smart contract code or on-chain verified contracts, performs deep analysis (static, symbolic, bytecode), and **generates comprehensive Foundry test suites** (unit, fuzz, invariant, integration PoCs). It runs them in a sandbox and exports ready-to-use test packs (ZIP or PR).

**Approach:** Combining formal methods, call graph traversal, fuzzing, RL-based attack simulation, and LLM-oriented test synthesis with clear proofs and artifacts.

**Principle:** Think like an attacker, act like a defender. Maximum utility for ethical white-hat hackers, zero exploitation without authorization.

---

## Features

- **Static Analysis:** AST/CFG/DFG parsing, role/privilege detection, SWC detectors, linters (Slither, Aderyn)
- **Bytecode Intelligence:** Disassembly, opcode semantics, basic blocks, SSA, taint analysis
- **Test Synthesis:** LLM + Foundry templates, contract/state mutations, property proposals
- **Fuzzing:** Adaptive coverage-guided fuzzing, grammar-aware ABI fuzzing, stateful sequences (Foundry + Echidna)
- **Symbolic Execution:** Mythril/Manticore/Z3 scenarios, bounded model checking
- **Attack Graph:** Call graph construction, access/permission traversal, attack chain composition
- **Reporting:** Markdown/PDF/JSON SARIF, GitHub PR comments, Code Scanning alerts
- **Export:** ZIP archives, GitHub PR integration, CLI client

---

## Architecture

Monorepo with three main planes:

- **Frontend:** Next.js + React + Tailwind + shadcn/ui + Monaco Editor, i18n (uk/en/fr)
- **Orchestrator/AI:** Python (FastAPI) for AI workers, queues, job scheduler
- **Engines:** Rust services for intensive tasks (AST/CFG, fuzz, mutations, call graphs)
- **3rd-party Tools:** Foundry (forge/anvil/cast), Slither, Mythril/Manticore, Echidna, Aderyn, Semgrep rules, solc/yul, ethers-rs/ethers.js
- **Storage:** PostgreSQL (metadata), Redis (queues/cache), MinIO/S3 (artifacts), optional: Neo4j (call/data graphs)
- **Message Queue:** NATS or RabbitMQ
- **Containers:** Docker Compose for dev, Helm chart for prod

### Services

1. **api-gateway** (FastAPI): REST+WebSocket; authentication (JWT/OAuth)
2. **analysis-planner** (Python): builds analysis plan (static → bytecode → fuzz → symbolic → RL/attack-graph)
3. **static-intel** (Rust + Slither API): parsing, AST/CFG/DFG, roles/privileges, SWC detectors, linters
4. **bytecode-intel** (Rust): bytecode extraction, disassembler, opcode semantics, basic-blocks, SSA, taint analysis
5. **test-synth** (Python+Rust): test generation (LLM + Foundry templates), contract/state mutations, property proposals
6. **fuzz-runner** (Rust): forge fuzz/invariant orchestration + Echidna bridge, coverage, counterexample reduction
7. **symbolic-runner** (Python): Mythril/Manticore/Z3 scenarios, bounded model checking on selected paths
8. **attack-graph** (Rust): call/access/permission graph construction and traversal, attack chain composition
9. **reporter** (Python): Markdown/PDF/JSON SARIF, GitHub PR comments, Code Scanning alerts
10. **delivery** (Node/TS): ZIP exports, Gist/PR integrations, CLI client

---

## Quickstart

### Prerequisites

- Docker & Docker Compose
- Node.js 22+
- Python 3.11+
- Rust 1.75+
- Foundry (forge, anvil, cast)

### Local Development

```bash
# Clone the repository
git clone https://github.com/VolodymyrStetsenko/rukh.git
cd rukh

# Start all services
make up

# Seed demo vulnerable contracts
make seed-demo

# Run end-to-end tests
make e2e

# Open the web UI
open http://localhost:3000
```

### Using the CLI

```bash
# Pull test artifacts for a job
rukh pull <job-id> --format=foundry

# Run exported tests
cd rukh-tests
forge install && forge build && forge test -vvv
```

---

## Repository Structure

```
rukh/
  apps/
    web/                 # Next.js (i18n, shadcn/ui, Monaco)
    api-gateway/         # FastAPI
    delivery/            # TS service: export/PR/gist/CLI API
  services/
    analysis-planner/    # Python planner
    static-intel/        # Rust + Slither bridge
    bytecode-intel/      # Rust EVM analysis
    test-synth/          # Python+Rust LLM + templating Foundry tests
    fuzz-runner/         # Rust orchestration forge/echidna
    symbolic-runner/     # Python Mythril/Manticore/Z3
    attack-graph/        # Rust attack path engine
    reporter/            # Python report builders (MD/PDF/SARIF)
  integrations/
    foundry/             # templates, foundry.toml, scripts
    slither/
    mythril/
    echidna/
  packages/
    rukhspec/            # JSONSchema/DSL + validators
    ui-kit/              # shared React components
    client-js/           # SDK/CLI TS
  deployments/
    docker/              # docker-compose.yml
    helm/                # Kubernetes Helm chart
  docs/
    handbook/
    api/
  bench/
    ethernaut/
    dvdefi/
    paradigm-ctf/
  .github/workflows/
  SECURITY.md
  CONTRIBUTING.md
  LICENSE
```

---

## Test Types

RUKH generates more than "ordinary" tests:

1. **Unit/Property tests** (Foundry): positive/negative, property-oriented with generators
2. **Fuzz:** Adaptive fuzz (coverage-guided), grammar-fuzz (ABI aware), stateful sequences
3. **Invariant:** Global protocol invariants (balance conservation, roles, emission limits, pool net-profit, etc.)
4. **Symbolic/SMT:** Path conditions, reachability of "bad states", minimal counterexample generation
5. **Attack-Graph Sequences:** Call chain construction (router/adapter/permit/flash positions), token behavior merging (fee-on-transfer, rebasing)
6. **MEV/Ordering:** Mempool/transaction order shuffling, sandwich/arbitrage scenarios, reentrancy under gas stress
7. **Mutation Testing:** Mutations of require/unchecked/arithmetics/storage-layout, test sensitivity verification
8. **Cross-Chain/Bridge:** Cross-chain message/address modeling, delays, retries, replay/nonce failures
9. **Oracle/Price:** Price feed drift or failures, delays, precision traps
10. **Access Control:** Role escalation, delegatecall/proxy traps, uncovered onlyOwner, UUPS/Beacon config
11. **Gas/DoS:** Worst-case and loops, granular gas profiles, griefing attacks
12. **State Desynchronization:** Multi-pool/adapter desync, rounding/precision attacks
13. **LLM-Discovered Hypotheses:** Generation of novel assumptions with automatic formalization into properties

Test catalog is tagged with SWC-ID/classifier (reentrancy, auth, overflow, bypass, rogue external call, arbitrary call, etc.).

---

## Integrations

- **Foundry:** generation of `*.t.sol`, `foundry.toml`, running `forge test`, invariants, fuzz, coverage
- **Aderyn/Slither:** static detectors with mapping → test recipes
- **Etherscan/Sourcify:** import of verified contracts/ABI
- **Tenderly/Anvil Forks:** fork environment for integration attacks
- **GitHub/GitLab:** PR bot, CI templates, Code Scanning (SARIF)
- **Walletless sim:** built-in signer for tests; no access to user private keys

---

## Security & Ethics

- **Threat Profile:** Multi-tenant SaaS, namespace isolation, read-only mounts, no-net by default
- **Acceptable Use Policy:** Automated detection of unauthorized on-chain targets → block
- **Red Buttons:** wipe, revoke, KMS rotate
- **Compliance Logs:** PII excluded

**Authorization Required:** Use only on your own or authorized targets. See [SECURITY.md](SECURITY.md).

---

## Monetization

- **Free:** Limited projects/minimal CPU-minute limit, no forks
- **Pro (individual):** Full test synthesis, forks, private artifacts, 5 parallel jobs
- **Team:** Seats, org repositories, SSO, policies
- **Enterprise / On-prem:** Air-gapped, node licensing
- **Marketplace:** Paid "rule/invariant packs" from experts
- **Bounty-Hub:** Clients post targets, auditors run RUKH packs

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT License](LICENSE)

---

## Author

**Volodymyr Stetsenko** (Zero2Auditor)

---

## Roadmap

- [ ] v0.1.0: MVP with basic static analysis and Foundry test generation
- [ ] v0.2.0: Fuzzing and invariant testing
- [ ] v0.3.0: Symbolic execution and attack graph
- [ ] v0.4.0: GitHub integration and SARIF reporting
- [ ] v1.0.0: Production-ready with full feature set

---

## Support

For issues, questions, or feature requests, please open an issue on [GitHub Issues](https://github.com/VolodymyrStetsenko/rukh/issues).

---

**RUKH** — Move forward in security.

