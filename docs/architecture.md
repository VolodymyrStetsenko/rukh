> # RUKH Platform Architecture
> 
> **Author:** Volodymyr Stetsenko (Zero2Auditor)
> 
> ---
> 
> ## 1. Overview
> 
> RUKH is built on a microservices architecture designed for scalability, performance, and security. It consists of three main logical planes:
> 
> -   **Frontend Plane:** The user interface, built with Next.js, for interacting with the platform.
> -   **Orchestration/AI Plane:** The core logic, written in Python, for managing analysis jobs, queuing tasks, and applying AI/LLM for test synthesis.
> -   **Engines Plane:** High-performance analysis services, written in Rust, for CPU-intensive tasks like static analysis, fuzzing, and symbolic execution.
> 
> The system is designed to be deployed in containers (Docker/Kubernetes) and uses a message queue (NATS) for asynchronous communication between services.
> 
> ## 2. System Components
> 
> ### 2.1. Frontend
> 
> -   **Framework:** Next.js with App Router
> -   **UI Library:** React, shadcn/ui, Tailwind CSS
> -   **Code Editor:** Monaco Editor for displaying code and analysis results.
> -   **Internationalization:** `next-intl` for multi-language support (uk/en/fr).
> 
> ### 2.2. Backend Services
> 
> -   **API Gateway (`api-gateway`):**
>     -   **Language:** Python (FastAPI)
>     -   **Function:** Main entry point for all API requests (REST + WebSocket).
>     -   **Responsibilities:** Authentication (JWT/OAuth), request validation, routing to internal services.
> 
> -   **Analysis Planner (`analysis-planner`):**
>     -   **Language:** Python
>     -   **Function:** Constructs a step-by-step analysis plan for each job.
>     -   **Logic:** Determines the sequence of analysis (e.g., `static` -> `bytecode` -> `fuzz` -> `symbolic`).
> 
> -   **Test Synthesizer (`test-synth`):**
>     -   **Language:** Python + Rust
>     -   **Function:** Generates Foundry test cases using LLMs and predefined templates.
>     -   **Responsibilities:** Proposes properties, mutates contract state, and generates unit, fuzz, and invariant tests.
> 
> -   **Reporter (`reporter`):**
>     -   **Language:** Python
>     -   **Function:** Aggregates results from all analysis phases and generates reports.
>     -   **Formats:** Markdown, PDF, JSON (SARIF).
> 
> ### 2.3. Analysis Engines (Rust)
> 
> -   **Static Intelligence (`static-intel`):**
>     -   **Function:** Performs static analysis on Solidity source code.
>     -   **Integrations:** Uses Slither, Aderyn, and custom detectors.
>     -   **Analysis:** AST/CFG/DFG parsing, role/privilege detection, SWC classification.
> 
> -   **Bytecode Intelligence (`bytecode-intel`):**
>     -   **Function:** Analyzes EVM bytecode.
>     -   **Analysis:** Disassembly, opcode semantics, basic block construction, taint analysis.
> 
> -   **Fuzz Runner (`fuzz-runner`):**
>     -   **Function:** Orchestrates fuzzing campaigns.
>     -   **Integrations:** Manages Foundry `forge fuzz` and Echidna.
>     -   **Logic:** Coverage-guided, adaptive, and stateful fuzzing.
> 
> -   **Symbolic Runner (`symbolic-runner`):**
>     -   **Function:** Runs symbolic execution tasks.
>     -   **Integrations:** Uses Mythril, Manticore, and Z3.
>     -   **Analysis:** Bounded model checking, path condition solving, counter-example generation.
> 
> -   **Attack Graph (`attack-graph`):**
>     -   **Function:** Builds and traverses graphs to find attack paths.
>     -   **Analysis:** Composes call chains, models access control, and identifies complex attack sequences.
> 
> ### 2.4. Data & Infrastructure
> 
> -   **Database:** PostgreSQL for persistent metadata (jobs, users, results).
> -   **Cache & Queue:** Redis for caching and short-lived data; NATS for message queuing.
> -   **Object Storage:** MinIO/S3 for storing artifacts (source code, test files, reports).
> -   **Graph Database (Optional):** Neo4j for storing and querying complex call graphs.
> -   **Deployment:** Docker Compose for local development, Helm chart for Kubernetes production.
> 
> ## 3. Data Flow Diagram
> 
> ```mermaid
> graph TD
>     subgraph User
>         A[Browser/CLI] --> B{API Gateway}
>     end
> 
>     subgraph RUKH Platform
>         B --> C[Analysis Planner]
>         B --> D{NATS Message Queue}
>         C --> D
> 
>         D --> E[Static Intel]
>         D --> F[Bytecode Intel]
>         D --> G[Fuzz Runner]
>         D --> H[Symbolic Runner]
>         D --> I[Attack Graph]
>         
>         subgraph Analysis Engines
>             E -- Results --> J{PostgreSQL}
>             F -- Results --> J
>             G -- Results --> J
>             H -- Results --> J
>             I -- Results --> J
>         end
> 
>         J --> K[Reporter]
>         K -- Report --> L{MinIO/S3}
>         B -- Fetch Report --> L
>         B -- Fetch Status --> M{Redis Cache}
>     end
> 
>     style User fill:#222,stroke:#333,stroke-width:2px
>     style B fill:#4A9,stroke:#333,stroke-width:2px
> ```
> 
> ## 4. Technology Stack
> 
> | Category          | Technology                                      |
> | ----------------- | ----------------------------------------------- |
> | **Frontend**      | Next.js, React, TypeScript, Tailwind CSS        |
> | **Backend**       | Python (FastAPI), Rust                          |
> | **Databases**     | PostgreSQL, Redis, MinIO, Neo4j (optional)      |
> | **Messaging**     | NATS                                            |
> | **Containerization**| Docker, Kubernetes (Helm)                       |
> | **CI/CD**         | GitHub Actions                                  |
> | **Testing Tools** | Foundry, Slither, Mythril, Manticore, Echidna   |
> 
> ---
> 
> *This document provides a high-level overview. For detailed service APIs and data models, refer to the respective service documentation.*

