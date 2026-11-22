/* global __GOOGLE_CLIENT_ID__, __OUTLOOK_CLIENT_ID__ */

const GMAIL_READONLY_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly';

export const isOutlookEnabled = Boolean(__OUTLOOK_CLIENT_ID__);

export function requestGmailToken() {
  const clientId = __GOOGLE_CLIENT_ID__;
  if (!clientId) {
    return Promise.reject(
      new Error(
        'Missing OAUTH_CLIENT_ID in root .env (or VITE_GOOGLE_CLIENT_ID).'
      )
    );
  }

  const oauth2 = window.google?.accounts?.oauth2;
  if (!oauth2) {
    return Promise.reject(
      new Error(
        'Google Identity Services failed to load. Check your network connection and reload.'
      )
    );
  }

  return new Promise((resolve, reject) => {
    const tokenClient = oauth2.initTokenClient({
      client_id: clientId,
      scope: GMAIL_READONLY_SCOPE,
      callback: (response) => {
        if (response.error || !response.access_token) {
          reject(
            new Error(
              response.error_description ||
                response.error ||
                'Gmail authorization was cancelled.'
            )
          );
          return;
        }
        resolve(response.access_token);
      },
      error_callback: (err) => {
        reject(new Error(err.message || 'Gmail OAuth popup closed.'));
      },
    });

    tokenClient.requestAccessToken({ prompt: 'consent' });
  });
}

export function revokeGmailToken(token) {
  if (!token) return;
  window.google?.accounts?.oauth2?.revoke(token, () => {});
}

export async function requestOutlookToken() {
  const clientId = __OUTLOOK_CLIENT_ID__;
  if (!clientId) {
    throw new Error(
      'Outlook OAuth is not configured yet (set VITE_OUTLOOK_CLIENT_ID in .env when ready).'
    );
  }
  throw new Error('Outlook MSAL flow will be wired once Entra Client ID is added.');
}

