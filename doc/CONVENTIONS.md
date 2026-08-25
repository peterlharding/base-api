# Conventions for Creating a New FastAPI API

* Use a pyproject.toml
* Add database scripts under db/schema in the root folder
* Use alembic for managing the database configuration and versioning
* Put alembic files in the db folder
* Add scripts under scripts in the root folder
* Add tests under test in the root folder
* Add documentation under doc in the project root
* Use 'uv' for python venv and installations (see Makefile)
* Put all the docker related setup under docker
* Use semantic versioning (see pyproject.toml)
* Release should be tagged (e.g. v0.3.0)
* Update CHANGELOG.md with every release
* Create more detailed release notes under release_notes (e.g. release_notes/v0.3.0.md)
