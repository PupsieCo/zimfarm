import abc
import datetime
import uuid

import jwt
from jwt import PyJWKClient
from jwt import exceptions as jwt_exceptions
from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from zimfarm_backend import logger
from zimfarm_backend.api.constants import (
    AUTH_MODES,
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
    OAUTH_AUDIENCE,
    OAUTH_ISSUER,
    OAUTH_JWKS_URI,
    OAUTH_MODE,
    OAUTH_OIDC_CLIENT_ID,
    OAUTH_OIDC_LOGIN_REQUIRE_2FA,
)
from zimfarm_backend.common.schemas import BaseModel


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    sub: uuid.UUID = Field(alias="subject")
    name: str | None = Field(exclude=True, default=None)


class TokenDecoder(abc.ABC):
    """Abstract base class for token decoders."""

    @abc.abstractmethod
    def decode(self, token: str) -> JWTClaims:
        """
        Decode and validate a token.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        Human-readable identifier of the decoder.
        """
        pass

    @property
    @abc.abstractmethod
    def can_decode(self) -> bool:
        """
        Check if this decoder can potentially decode the given token.
        """
        pass


class LocalTokenDecoder(TokenDecoder):
    """Decoder for local Zimfarm JWT tokens."""

    def __init__(self, secret: str = JWT_SECRET, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm

    def decode(self, token: str) -> JWTClaims:
        """
        Decode and validate a local Zimfarm token.
        """
        jwt_claims = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        return JWTClaims(**jwt_claims)

    @property
    def name(self) -> str:
        return "local"

    @property
    def can_decode(self) -> bool:
        return "local" in AUTH_MODES


class OAuthOIDCTokenDecoder(TokenDecoder):
    """Decoder for OAuth OIDC JWT tokens."""

    def __init__(self):
        """Initialize OAuth token decoder."""
        self._jwks_client = PyJWKClient(
            OAUTH_JWKS_URI,
            cache_keys=True,
            headers={"User-Agent": "PyJWT/2.11.0"},
        )

    def decode(self, token: str) -> JWTClaims:
        """
        Decode and validate an OAuth OIDC token.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            issuer=OAUTH_ISSUER,
            audience=OAUTH_OIDC_CLIENT_ID,
            options={
                "require": ["exp", "iat", "iss", "sub", "name", "amr", "aud"],
            },
        )

        # Ensure the user logged in with two authentication factors. As per Ory docs,
        # "password", "code"  and "oidc" are categorized as first methods of login while
        # "totp", "webauthn" and "lookup_secret" are second authentication methods
        # https://www.ory.com/docs/kratos/mfa/overview#authenticator-assurance-level-aal
        amr = set(decoded_token.get("amr", []))
        if OAUTH_OIDC_LOGIN_REQUIRE_2FA and not (
            {"password", "oidc", "code"} & amr
            and {"webauthn", "lookup_secrets", "totp"} & amr
        ):
            raise ValueError(
                "2FA authentication is mandatory on Zimfarm but it looks like you only "
                "have one setup on Ory. Please, configure a second one on Ory at "
                "https://login.kiwix.org/settings"
            )
        return JWTClaims.model_validate(decoded_token)

    @property
    def name(self) -> str:
        return "oauth-oidc"

    @property
    def can_decode(self) -> bool:
        return "oauth-oidc" in AUTH_MODES


class RAuthyTokenDecoder(TokenDecoder):
    """Decoder for RAuthy OIDC JWT tokens."""

    def __init__(self):
        """Initialize RAuthy token decoder."""
        self._jwks_client = PyJWKClient(
            OAUTH_JWKS_URI,
            cache_keys=True,
            headers={"User-Agent": "PyJWT/2.11.0"},
        )

    def decode(self, token: str) -> JWTClaims:
        """
        Decode and validate a RAuthy OIDC token.

        RAuthy uses the /oidc/ endpoints with EdDSA/RS256 signing algorithms.
        The token validation is similar to OAuthOIDCTokenDecoder but may have
        different issuer and audience values.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            issuer=OAUTH_ISSUER,
            # Use OAUTH_AUDIENCE if set, otherwise fall back to OAUTH_OIDC_CLIENT_ID
            audience=OAUTH_AUDIENCE or OAUTH_OIDC_CLIENT_ID,
            options={
                "require": ["exp", "iat", "iss", "sub", "name", "amr", "aud"],
            },
        )

        # RAuthy uses 'amr' claim for authentication methods verification
        # amr values: password, oidc, code, totp, webauthn, lookup_secret
        amr = set(decoded_token.get("amr", []))
        if OAUTH_OIDC_LOGIN_REQUIRE_2FA and not (
            {"password", "oidc", "code"} & amr
            and {"webauthn", "lookup_secrets", "totp"} & amr
        ):
            raise ValueError(
                "2FA authentication is mandatory on Zimfarm but it looks like you only "
                "have one setup. Please, configure a second authentication factor."
            )
        return JWTClaims.model_validate(decoded_token)

    @property
    def name(self) -> str:
        return "rauthy"

    @property
    def can_decode(self) -> bool:
        return "rauthy" in AUTH_MODES


class TokenDecoderChain:
    """Chain of responsibility for token decoders."""

    def __init__(self, decoders: list[TokenDecoder]):
        """
        Initialize decoder chain.
        """
        self.decoders = decoders

    def decode(self, token: str) -> JWTClaims:
        """
        Try to decode token using each decoder in order.
        """
        exc_cls: Exception | None = None
        decoders = [decoder for decoder in self.decoders if decoder.can_decode]
        if not decoders:
            raise ValueError("No decoders registered for decoding token.")

        for decoder in decoders:
            if decoder.can_decode:
                try:
                    return decoder.decode(token)
                except (
                    jwt_exceptions.PyJWTError,
                    PydanticValidationError,
                    Exception,
                ) as exc:
                    logger.debug(f"{decoder.name}: unable to decode token: {exc!s}")
                    # keep track of the most recent exception class
                    exc_cls = exc

        if exc_cls:
            raise exc_cls

        raise ValueError("Inavlid token")


# Token decoder chain order: Local first, then OIDC/rauthy
# Session-based auth has been removed in favor of OIDC Authorization Code flow
token_decoder = TokenDecoderChain(
    decoders=[
        LocalTokenDecoder(),
        OAuthOIDCTokenDecoder(),
        RAuthyTokenDecoder(),
    ]
)


def generate_access_token(
    *,
    user_id: str,
    issue_time: datetime.datetime,
) -> str:
    """Generate a JWT access token for the given user ID with configured expiry."""

    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")
