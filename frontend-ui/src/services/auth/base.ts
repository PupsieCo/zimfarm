import type { Config } from '@/config'
import type { StoredToken } from '@/types/auth'

export interface OAuthConfig {
  clientId: string
  authorizeUrl: string
  tokenUrl: string
  userInfoUrl: string
  revocationUrl: string
  basePath: string
  issuer: string
}

/**
 * Get OIDC authentication configuration from app config
 * Supports both RAuthy and other OIDC providers
 */
export function getOAuthConfig(config: Config): OAuthConfig {
  const basePath = config.OAUTH_BASE_URL
  const issuer = config.OAUTH_ISSUER || `${basePath}/auth/v1`

  // Use standard OIDC paths (compatible with RAuthy and most OIDC providers)
  return {
    clientId: config.OAUTH_CLIENT_ID,
    authorizeUrl: `${basePath}/oidc/authorize`,
    tokenUrl: `${basePath}/oidc/token`,
    userInfoUrl: `${basePath}/oidc/userinfo`,
    revocationUrl: `${basePath}/oidc/token/revoke`,
    basePath: basePath,
    issuer: issuer,
  }
}

/**
 * Abstract base class for authentication providers
 * Defines the common interface that all auth providers must implement
 */
export abstract class AuthProvider {
  /**
   * Initiates the login flow
   */
  abstract initiateLogin(username?: string, password?: string): Promise<void>

  /**
   * Handles the logout process
   */
  abstract logout(accessToken?: string): Promise<void>

  /**
   * Refreshes the authentication credentials
   */
  abstract refreshAuth(refreshToken: string): Promise<StoredToken>

  /**
   * Handles the authentication callback from the auth provider
   */
  abstract onCallback(callbackUrl: string): Promise<StoredToken>

  /**
   * Save the token from the auth provider
   */
  abstract saveToken(token: StoredToken): null

  /**
   * Load auth token
   */
  abstract loadToken(): Promise<StoredToken | null>

  abstract removeToken(): void
}
