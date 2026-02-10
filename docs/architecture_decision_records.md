# ADR 001: System Architecture Design

**Status:** Accepted

## Context
We need a system that consolidates disparate Excel data into a unified dashboard for trend analysis. The team is small, and the timeline is short (weeks/months).

## Decision
We will implement a **Client-Server Monolith** using **Layered Architecture**.

### The Five Dimensions:
1.  **System Roles:** **Client-Server.** Backend handles Excel parsing; Frontend handles visualization.
2.  **Deployment:** **Monolith.** API and UI are bundled together for deployment simplicity.
3.  **Code Organization:** **Layered.** Separate layers for Data Ingestion (Excel), Domain Logic (Trend Calculation), and Presentation (Charts).
4.  **Data Ownership:** **Single Database.** A central staging database (SQLite) holds reconciled data.
5.  **Interaction:** **Synchronous.** Data is fetched immediately upon user request.

## Alternatives Considered
* **Event-Driven:** Rejected due to excessive complexity for file-based processing.
* **Microservices:** Rejected as it would require more developers and infrastructure management.

## Consequences
* **Positive:** Easy to maintain by 1-2 people; unified logic for data reconciliation.
* **Negative:** Scaling to millions of rows may require moving from SQLite to a dedicated server (PostgreSQL).
