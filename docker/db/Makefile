

# -----------------------------------------------------------------------------

up:
	docker compose up -d
	docker ps

down:
	docker compose down
	sleep 1
	docker ps

# Create the application roles and the base-api database (see SETUP.md).
# Requires DB_PASSWORD in the environment, e.g.:
#   set -a; . ../../.env; set +a
setup:
	docker exec -i base-db psql -U postgres -v db_password=$(DB_PASSWORD) < 01-create-users.sql
	docker exec -i base-db psql -U postgres < 02-create-database.sql
	docker exec -i base-db psql -U postgres -d base_api < 03-create-application_user.sql




