import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Hook for blocking navigation when form has unsaved changes
 *
 * Features:
 * - Blocks browser back/forward buttons
 * - Triggers callback when navigation is blocked
 * - Handles popstate events to prevent navigation
 *
 * Note: This implementation uses browser history manipulation.
 * For React Router internal navigation, additional handling may be needed.
 *
 * @param shouldBlock - Whether navigation should be blocked
 * @param onBlock - Callback function to execute when navigation is blocked
 */
export const useNavigationBlocker = (
  shouldBlock: boolean,
  onBlock: () => void
): void => {
  const location = useLocation();

  useEffect(() => {
    // Handle browser back/forward buttons
    const handlePopState = (e: PopStateEvent) => {
      if (shouldBlock) {
        // Prevent the navigation
        e.preventDefault();

        // Push current state back to history to "undo" the back navigation
        window.history.pushState(null, '', location.pathname);

        // Trigger the block callback (show modal)
        onBlock();
      }
    };

    if (shouldBlock) {
      // Push a state to create a history entry that we can intercept
      window.history.pushState(null, '', location.pathname);

      // Listen for popstate events (back/forward button clicks)
      window.addEventListener('popstate', handlePopState);

      console.log('[useNavigationBlocker] Navigation blocking activated');
    }

    return () => {
      window.removeEventListener('popstate', handlePopState);
      if (shouldBlock) {
        console.log('[useNavigationBlocker] Navigation blocking deactivated');
      }
    };
  }, [shouldBlock, location, onBlock]);
};

/**
 * Hook for detecting beforeunload event (tab/window close)
 *
 * Shows browser's default confirmation dialog when user tries to close
 * the tab or navigate away from the page.
 *
 * @param shouldWarn - Whether to show warning on page unload
 * @param message - Optional custom message (note: most browsers ignore this)
 */
export const useBeforeUnload = (
  shouldWarn: boolean,
  message: string = 'You have unsaved changes. Are you sure you want to leave?'
): void => {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (shouldWarn) {
        // Modern browsers ignore custom messages and show their own
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    };

    if (shouldWarn) {
      window.addEventListener('beforeunload', handleBeforeUnload);
      console.log('[useBeforeUnload] Unload warning activated');
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (shouldWarn) {
        console.log('[useBeforeUnload] Unload warning deactivated');
      }
    };
  }, [shouldWarn, message]);
};
