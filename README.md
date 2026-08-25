# base-api

A basic API implemented using FastAPI

See doc/* in the root folder for more extensive documentation


## Testing

The test suite runs against a dedicated Postgres container (never the dev
database).  See [doc/TESTING.md](doc/TESTING.md) for the details; the short
version:

```sh
make test
```
