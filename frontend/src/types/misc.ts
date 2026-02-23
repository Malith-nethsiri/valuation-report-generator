/**
 * Miscellaneous types: ApiError, HealthResponse, AdjacentDateResponse.
 */

export interface ApiError {
  detail: string;
}

export interface HealthResponse {
  status: string;
  message: string;
}

// Letterhead Template Types
export interface AdjacentDateResponse {
  adjacent_date: string | null;
}

// ===== VEHICLE TYPES =====
