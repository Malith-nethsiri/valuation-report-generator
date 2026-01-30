import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sentryVitePlugin } from '@sentry/vite-plugin'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  const sentryAuthToken = process.env.SENTRY_AUTH_TOKEN
  const sentryOrg = process.env.SENTRY_ORG
  const sentryProject = process.env.SENTRY_PROJECT

  // Only enable source maps in production if Sentry is configured
  // This prevents exposing source code when error tracking is not set up
  const hasSentryConfig = Boolean(sentryAuthToken && sentryOrg && sentryProject)
  const enableSourceMaps = isProduction ? hasSentryConfig : true

  return {
    plugins: [
      react(),
      // Only include Sentry plugin in production with required env vars
      isProduction && hasSentryConfig
        ? sentryVitePlugin({
            org: sentryOrg,
            project: sentryProject,
            authToken: sentryAuthToken,
            sourcemaps: {
              // Delete source maps after uploading to Sentry
              // This prevents them from being served to clients
              filesToDeleteAfterUpload: ['**/*.map'],
            },
            telemetry: false,
          })
        : null,
    ].filter(Boolean),
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      // Only generate source maps if:
      // - Development mode (for debugging)
      // - Production with Sentry configured (maps are uploaded then deleted)
      sourcemap: enableSourceMaps,
    },
  }
})
