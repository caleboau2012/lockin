/* global __API_BASE_URL__ */

import { SAMPLE_AUDIT_RESPONSE } from './mockAudit';

export async function fetchAuditReport(provider, accessToken) {
  if (provider === 'mock') {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return SAMPLE_AUDIT_RESPONSE;
  }

  const apiUrl = `${__API_BASE_URL__}/api/audit`;

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        access_token: accessToken ?? '',
      }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      const detail =
        errorBody?.detail || `Audit request failed (HTTP ${response.status}).`;
      throw new Error(detail);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof TypeError) {
      throw new Error(
        `Could not connect to the LockIn backend (${__API_BASE_URL__}). Make sure the FastAPI server is running on port 8000.`
      );
    }
    throw err;
  }
}
