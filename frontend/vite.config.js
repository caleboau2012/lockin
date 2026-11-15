import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const rootDir = path.resolve(__dirname, '..');
  const env = loadEnv(mode, rootDir, '');

  // Only expose safe public client IDs/URLs — never OAUTH_CLIENT_SECRET or GEMINI_API_KEY
  const googleClientId = env.VITE_GOOGLE_CLIENT_ID || env.OAUTH_CLIENT_ID || '';
  const outlookClientId = env.VITE_OUTLOOK_CLIENT_ID || '';
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000';

  return {
    plugins: [react()],
    define: {
      __GOOGLE_CLIENT_ID__: JSON.stringify(googleClientId),
      __OUTLOOK_CLIENT_ID__: JSON.stringify(outlookClientId),
      __API_BASE_URL__: JSON.stringify(apiBaseUrl),
    },
    server: {
      port: 5173,
      strictPort: true,
    },
  };
});

