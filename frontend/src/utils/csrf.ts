/**
 * CSRF token helper — single source of truth.
 * Imported by all components and services that need to attach the CSRF token.
 */
export const getCSRFToken = (): string | null => {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
};
