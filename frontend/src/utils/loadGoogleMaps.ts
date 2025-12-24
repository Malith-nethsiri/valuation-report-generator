/**
 * Utility to load Google Maps JavaScript API dynamically
 */

let isLoading = false;
let isLoaded = false;
const callbacks: Array<() => void> = [];

export function loadGoogleMapsScript(apiKey: string): Promise<void> {
  return new Promise((resolve, reject) => {
    // Already loaded
    if (typeof google !== 'undefined' && google.maps) {
      isLoaded = true;
      resolve();
      return;
    }

    // Currently loading - add to callback queue
    if (isLoading) {
      callbacks.push(resolve);
      return;
    }

    // Start loading
    isLoading = true;

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      isLoaded = true;
      isLoading = false;
      resolve();
      // Call all queued callbacks
      callbacks.forEach(cb => cb());
      callbacks.length = 0;
    };

    script.onerror = () => {
      isLoading = false;
      const error = new Error('Failed to load Google Maps script');
      reject(error);
      console.error('Failed to load Google Maps API');
    };

    document.head.appendChild(script);
  });
}

export function isGoogleMapsLoaded(): boolean {
  return isLoaded && typeof google !== 'undefined' && !!google.maps;
}
