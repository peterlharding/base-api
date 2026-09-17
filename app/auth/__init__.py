#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Authentication.

Kept as a package marker on purpose.  This file is executed by any
``app.auth.*`` import, so anything that fails here takes the whole package
with it - which is what happened when it carried module-level imports of
its own.

    app/auth/password.py   bcrypt hashing, used by the models and the seed
    app/auth/handler.py    JWT sign and decode
    app/auth/bearer.py     JWTBearer dependency for protecting routes

The two-layer flow on POST /api/v1/auth/authenticate:

    HTTP Basic     -> api_credentials    (which client is calling)
    JSON body      -> application_user   (which user is signing in)

Both must pass before a token is issued.
"""
# -----------------------------------------------------------------------------
