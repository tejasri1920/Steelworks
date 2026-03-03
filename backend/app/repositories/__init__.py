# app/repositories/__init__.py
# The repository layer is responsible for all database access.
# It isolates SQL/ORM queries from the HTTP routing layer so business
# logic is easy to test without a live HTTP server.
