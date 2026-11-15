/* global __API_BASE_URL__ */

import { SAMPLE_AUDIT_RESPONSE } from './mockAudit';

export async function fetchAuditReport(provider, accessToken) {
  const apiUrl = `${__API_BASE_URL__}/api/audit`;

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        access_token: accessToken ?? null,
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
    // In local mock mode, fall back cleanly to built-in sample data if backend isn't running yet
    if (provider === 'mock' && err instanceof TypeError) {
      await new Promise((resolve) => setTimeout(resolve, 650));
      return SAMPLE_AUDIT_RESPONSE;
    }
    throw err;
  }
}

