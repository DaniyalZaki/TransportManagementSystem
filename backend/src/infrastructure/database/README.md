# Database boundary

The backend is the only component that connects to PostgreSQL. Feature modules
own their own SQL and migration files; no client connects to the database.
Migrations are handwritten SQL and are applied in lexical order by the local
development command described in the root README.
