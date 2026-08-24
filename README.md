# base-api
A basic APIU implemented using FastAPI

## Testing

The test suite runs against a dedicated Postgres container (never the dev
database).  See [doc/TESTING.md](doc/TESTING.md) for the details; the short
version:

```sh
make test
```
