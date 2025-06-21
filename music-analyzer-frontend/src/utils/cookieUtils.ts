import Cookies from 'js-cookie';

const AUTH_COOKIE_NAME = 'music_analyzer_auth';
const COOKIE_EXPIRY_DAYS = 14; // 2 weeks

interface AuthData {
  username: string;
  password: string;
}

export const cookieUtils = {
  // Set authentication cookie
  setAuthCookie: (username: string, password: string): void => {
    const authData: AuthData = { username, password };
    const encodedData = btoa(JSON.stringify(authData));
    
    Cookies.set(AUTH_COOKIE_NAME, encodedData, {
      expires: COOKIE_EXPIRY_DAYS,
      secure: window.location.protocol === 'https:',
      sameSite: 'strict',
      // httpOnly cannot be set from JavaScript for security reasons
    });
  },

  // Get authentication data from cookie
  getAuthCookie: (): AuthData | null => {
    const encodedData = Cookies.get(AUTH_COOKIE_NAME);
    if (!encodedData) {
      return null;
    }

    try {
      const decodedData = atob(encodedData);
      return JSON.parse(decodedData) as AuthData;
    } catch (error) {
      console.error('Failed to decode auth cookie:', error);
      // Remove invalid cookie
      Cookies.remove(AUTH_COOKIE_NAME);
      return null;
    }
  },

  // Remove authentication cookie
  removeAuthCookie: (): void => {
    Cookies.remove(AUTH_COOKIE_NAME);
  },

  // Get the auth header from cookie
  getAuthHeaderFromCookie: (): string => {
    const authData = cookieUtils.getAuthCookie();
    if (authData) {
      return 'Basic ' + btoa(`${authData.username}:${authData.password}`);
    }
    return '';
  },
};