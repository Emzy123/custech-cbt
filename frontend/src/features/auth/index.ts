/** Matches `localStorage` key used in `lib/api.ts` (SimpleJWT access token). */
export const TOKEN_KEY = 'authToken';

export const authEndpoints = {
  login: '/api/v1/auth/login',
  refresh: '/api/v1/auth/refresh',
  register: '/api/v1/auth/register',
};
