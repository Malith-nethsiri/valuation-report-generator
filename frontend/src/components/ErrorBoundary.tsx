import React, { Component, ErrorInfo, ReactNode } from 'react';
import * as Sentry from '@sentry/react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  eventId: string | null;
}

/**
 * ErrorBoundary component catches React errors and provides graceful fallback UI
 * Prevents blank screens and provides recovery options
 * Reports errors to Sentry in production
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('ErrorBoundary caught error:', error, errorInfo);

    // Call optional error callback
    this.props.onError?.(error, errorInfo);

    // Report to Sentry in production
    const IS_PRODUCTION = import.meta.env.MODE === 'production';
    const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;

    if (SENTRY_DSN && IS_PRODUCTION) {
      Sentry.withScope((scope) => {
        scope.setExtras({
          componentStack: errorInfo.componentStack,
        });
        const eventId = Sentry.captureException(error);
        this.setState({ eventId });
      });
    }

    // Store error info in state
    this.setState({
      error,
      errorInfo
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null
    });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReportFeedback = () => {
    // Open Sentry user feedback dialog if available
    const { eventId } = this.state;
    if (eventId) {
      Sentry.showReportDialog({ eventId });
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const IS_PRODUCTION = import.meta.env.MODE === 'production';
      const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
      const showReportButton = IS_PRODUCTION && SENTRY_DSN && this.state.eventId;

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 text-red-600 mb-4">
              <AlertCircle className="h-8 w-8 flex-shrink-0" />
              <h1 className="text-2xl font-bold">Something went wrong</h1>
            </div>

            <p className="text-gray-600 mb-4">
              We're sorry, but an unexpected error occurred. This has been logged and we'll look into it.
            </p>

            <p className="text-sm text-gray-500 mb-6">
              You can try refreshing the page or returning to the home page.
            </p>

            {/* Development-only error details */}
            {!IS_PRODUCTION && this.state.error && (
              <details className="mb-4 p-3 bg-gray-100 rounded text-sm border border-gray-300">
                <summary className="cursor-pointer font-semibold text-gray-700 mb-2 hover:text-gray-900">
                  Error Details (Development Only)
                </summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <p className="font-semibold text-red-600">Error:</p>
                    <pre className="text-xs overflow-auto bg-white p-2 rounded border">
                      {this.state.error.toString()}
                    </pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <p className="font-semibold text-red-600">Component Stack:</p>
                      <pre className="text-xs overflow-auto bg-white p-2 rounded border max-h-48">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Action buttons */}
            <div className="flex flex-col gap-3">
              <div className="flex gap-3">
                <button
                  onClick={this.handleReset}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                >
                  <Home className="h-4 w-4" />
                  Go Home
                </button>
              </div>

              {/* Sentry feedback button (production only) */}
              {showReportButton && (
                <button
                  onClick={this.handleReportFeedback}
                  className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
                >
                  Report this issue
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
