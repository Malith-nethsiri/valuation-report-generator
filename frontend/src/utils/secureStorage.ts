/**
 * Secure storage utility using sessionStorage with AES encryption
 *
 * Benefits over localStorage:
 * - sessionStorage is cleared when browser tab closes (shorter exposure window)
 * - Encryption provides additional layer of protection against XSS
 * - Data is not persisted across browser sessions
 *
 * Note: This is NOT a complete XSS defense. Best practices include:
 * - Content Security Policy (CSP)
 * - Input sanitization
 * - Output encoding
 * - HttpOnly cookies (for production, consider migrating to this)
 */

import CryptoJS from 'crypto-js';

class SecureStorage {
  private encryptionKey: string;
  private storage: Storage;

  constructor(useSessionStorage = true) {
    // Generate encryption key from browser fingerprint + timestamp
    // In production, you might want to derive this from user session or server-provided key
    this.encryptionKey = this.generateEncryptionKey();
    this.storage = useSessionStorage ? sessionStorage : localStorage;
  }

  /**
   * Generate encryption key from browser fingerprint
   * Uses various browser properties to create a unique-ish key
   */
  private generateEncryptionKey(): string {
    const browserFingerprint = [
      navigator.userAgent,
      navigator.language,
      screen.colorDepth,
      screen.width,
      screen.height,
      new Date().getTimezoneOffset(),
    ].join('|');

    // Hash the fingerprint to create encryption key
    return CryptoJS.SHA256(browserFingerprint).toString();
  }

  /**
   * Encrypt data using AES-256
   */
  private encrypt(data: string): string {
    try {
      return CryptoJS.AES.encrypt(data, this.encryptionKey).toString();
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * Decrypt data using AES-256
   */
  private decrypt(encryptedData: string): string {
    try {
      const bytes = CryptoJS.AES.decrypt(encryptedData, this.encryptionKey);
      const decrypted = bytes.toString(CryptoJS.enc.Utf8);

      if (!decrypted) {
        throw new Error('Decryption resulted in empty string');
      }

      return decrypted;
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  /**
   * Store encrypted item
   */
  setItem(key: string, value: string): void {
    try {
      const encrypted = this.encrypt(value);
      this.storage.setItem(key, encrypted);
    } catch (error) {
      console.error(`Failed to store item '${key}':`, error);
      throw error;
    }
  }

  /**
   * Retrieve and decrypt item
   */
  getItem(key: string): string | null {
    try {
      const encrypted = this.storage.getItem(key);

      if (!encrypted) {
        return null;
      }

      return this.decrypt(encrypted);
    } catch (error) {
      console.error(`Failed to retrieve item '${key}':`, error);
      // If decryption fails, remove the corrupted item
      this.storage.removeItem(key);
      return null;
    }
  }

  /**
   * Remove item
   */
  removeItem(key: string): void {
    this.storage.removeItem(key);
  }

  /**
   * Clear all storage
   */
  clear(): void {
    this.storage.clear();
  }

  /**
   * Check if key exists
   */
  hasItem(key: string): boolean {
    return this.storage.getItem(key) !== null;
  }

  /**
   * Store JSON object (automatically serialized and encrypted)
   */
  setJSON<T>(key: string, value: T): void {
    try {
      const jsonString = JSON.stringify(value);
      this.setItem(key, jsonString);
    } catch (error) {
      console.error(`Failed to store JSON for '${key}':`, error);
      throw new Error('Failed to serialize and store JSON');
    }
  }

  /**
   * Retrieve JSON object (automatically decrypted and deserialized)
   */
  getJSON<T>(key: string): T | null {
    try {
      const jsonString = this.getItem(key);

      if (!jsonString) {
        return null;
      }

      return JSON.parse(jsonString) as T;
    } catch (error) {
      console.error(`Failed to retrieve JSON for '${key}':`, error);
      // Remove corrupted data
      this.removeItem(key);
      return null;
    }
  }

  /**
   * Store item with expiration time
   */
  setItemWithExpiry(key: string, value: string, expiryMs: number): void {
    const now = new Date().getTime();
    const item = {
      value: value,
      expiry: now + expiryMs,
    };
    this.setJSON(key, item);
  }

  /**
   * Get item with expiration check
   * Returns null if item expired
   */
  getItemWithExpiry(key: string): string | null {
    const item = this.getJSON<{ value: string; expiry: number }>(key);

    if (!item) {
      return null;
    }

    const now = new Date().getTime();

    // Check if expired
    if (now > item.expiry) {
      this.removeItem(key);
      return null;
    }

    return item.value;
  }

  /**
   * Get all keys in storage
   */
  getAllKeys(): string[] {
    const keys: string[] = [];
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i);
      if (key) {
        keys.push(key);
      }
    }
    return keys;
  }

  /**
   * Get storage size in bytes (approximate)
   */
  getStorageSize(): number {
    let total = 0;
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i);
      if (key) {
        const value = this.storage.getItem(key);
        if (value) {
          total += key.length + value.length;
        }
      }
    }
    // Multiply by 2 because JavaScript uses UTF-16 encoding (2 bytes per character)
    return total * 2;
  }
}

// Create singleton instances
export const secureSessionStorage = new SecureStorage(true);  // Uses sessionStorage (default)
export const secureLocalStorage = new SecureStorage(false);   // Uses localStorage (if needed)

// Export class for custom instances
export default SecureStorage;

// ===== AUTHENTICATION TOKEN HELPERS =====

const AUTH_TOKEN_KEY = 'authToken';
const USER_DATA_KEY = 'user';
const TOKEN_EXPIRY_MS = 24 * 60 * 60 * 1000; // 24 hours

export const authTokenStorage = {
  /**
   * Store authentication token (encrypted in sessionStorage)
   */
  setToken(token: string): void {
    secureSessionStorage.setItemWithExpiry(AUTH_TOKEN_KEY, token, TOKEN_EXPIRY_MS);
  },

  /**
   * Retrieve authentication token
   */
  getToken(): string | null {
    return secureSessionStorage.getItemWithExpiry(AUTH_TOKEN_KEY);
  },

  /**
   * Remove authentication token
   */
  removeToken(): void {
    secureSessionStorage.removeItem(AUTH_TOKEN_KEY);
  },

  /**
   * Check if token exists and is valid
   */
  hasValidToken(): boolean {
    return secureSessionStorage.getItemWithExpiry(AUTH_TOKEN_KEY) !== null;
  },

  /**
   * Store user data (encrypted in sessionStorage)
   */
  setUserData(userData: any): void {
    secureSessionStorage.setJSON(USER_DATA_KEY, userData);
  },

  /**
   * Retrieve user data
   */
  getUserData<T = any>(): T | null {
    return secureSessionStorage.getJSON<T>(USER_DATA_KEY);
  },

  /**
   * Remove user data
   */
  removeUserData(): void {
    secureSessionStorage.removeItem(USER_DATA_KEY);
  },

  /**
   * Clear all authentication data
   */
  clearAll(): void {
    this.removeToken();
    this.removeUserData();
  },
};
