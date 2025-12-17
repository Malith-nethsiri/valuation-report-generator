/**
 * One-time migration utility to clear legacy localStorage draft data
 *
 * This function removes the old auto-save data that was stored in localStorage
 * before the new draft system was implemented. It should be called once on
 * app initialization to clean up any existing user data.
 *
 * @returns void
 */
export const clearLegacyDrafts = (): void => {
  try {
    const hadDraft = localStorage.getItem('residentialFormDraft') !== null;
    const hadStep = localStorage.getItem('residentialFormStep') !== null;

    // Remove legacy draft data
    localStorage.removeItem('residentialFormDraft');
    localStorage.removeItem('residentialFormStep');

    if (hadDraft || hadStep) {
      console.log('[Migration] Cleared legacy localStorage drafts');
    }
  } catch (error) {
    // Silently fail if localStorage is not available or blocked
    console.error('[Migration] Failed to clear legacy drafts:', error);
  }
};
