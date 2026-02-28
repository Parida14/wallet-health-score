/**
 * API client for the Wallet Health Score FastAPI backend.
 * Provides typed functions for all API endpoints.
 */

import type { WalletScore, CompareRequest, CompareResponse, ExtractionJob } from '@/types/wallet';

/**
 * Base URL for the API - configurable via environment variable
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug: Log API URL in development (will be removed in production build)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[Wallet API] Using API URL:', API_BASE_URL);
}

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let detail: string | undefined;
      try {
        const errorData = await response.json();
        detail = errorData.detail;
      } catch {
        // Response body is not JSON
      }
      throw new ApiError(
        `API request failed: ${response.statusText}`,
        response.status,
        detail
      );
    }

    return response.json();
  } catch (error) {
    // Handle network errors (CORS, connection refused, etc.)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Network error: Unable to connect to API at ${API_BASE_URL}. Please ensure the API is running.`,
        0,
        error.message
      );
    }
    // Re-throw ApiError instances
    if (error instanceof ApiError) {
      throw error;
    }
    // Wrap other errors
    throw new ApiError(
      `Unexpected error: ${error instanceof Error ? error.message : String(error)}`,
      0,
      undefined
    );
  }
}

/**
 * Get the latest health score for a wallet address.
 * 
 * @param address - Ethereum wallet address (0x...)
 * @returns Wallet score data including component breakdown
 * @throws ApiError if wallet not found (404) or other errors
 * 
 * @example
 * const score = await getWalletScore('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045');
 * console.log(score.wallet_score); // 78.4
 */
export async function getWalletScore(address: string): Promise<WalletScore> {
  return fetchApi<WalletScore>(`/score/${address}`);
}

/**
 * Get historical health scores for a wallet address.
 * 
 * @param address - Ethereum wallet address (0x...)
 * @param days - Number of days of history to fetch (default: 30)
 * @returns Array of wallet scores ordered by date (most recent first)
 * @throws ApiError if wallet not found (404) or other errors
 * 
 * @example
 * const history = await getWalletHistory('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 7);
 * console.log(history.length); // Up to 7 days of data
 */
export async function getWalletHistory(
  address: string,
  days: number = 30
): Promise<WalletScore[]> {
  return fetchApi<WalletScore[]>(`/history/${address}?days=${days}`);
}

/**
 * Compare health scores across multiple wallet addresses.
 * 
 * @param addresses - Array of Ethereum wallet addresses (2-10 addresses)
 * @returns Comparison data including individual scores and statistics
 * @throws ApiError if no wallets found or other errors
 * 
 * @example
 * const comparison = await compareWallets([
 *   '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
 *   '0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe'
 * ]);
 * console.log(comparison.comparison.average_score);
 */
export async function compareWallets(
  addresses: string[]
): Promise<CompareResponse> {
  const request: CompareRequest = { addresses };
  return fetchApi<CompareResponse>('/compare', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Trigger on-demand extraction of wallet data.
 * The API returns 202 Accepted with a job object.
 *
 * @param address - Ethereum wallet address (0x...)
 * @returns Extraction job with status info
 *
 * @example
 * const job = await extractWallet('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045');
 * console.log(job.id, job.status); // "uuid" "pending"
 */
export async function extractWallet(address: string): Promise<ExtractionJob> {
  return fetchApi<ExtractionJob>(`/extract/${address}`, { method: 'POST' });
}

/**
 * Poll the status of an extraction job.
 *
 * @param jobId - UUID of the extraction job
 * @returns Current job status
 */
export async function getExtractionStatus(jobId: string): Promise<ExtractionJob> {
  return fetchApi<ExtractionJob>(`/extract/status/${jobId}`);
}

/**
 * Get the latest extraction job for a wallet address.
 *
 * @param address - Ethereum wallet address (0x...)
 * @returns Latest extraction job or throws 404
 */
export async function getExtractionStatusByAddress(address: string): Promise<ExtractionJob> {
  return fetchApi<ExtractionJob>(`/extract/status/address/${address}`);
}

/**
 * Check if the API is healthy and responding.
 * 
 * @returns true if API is healthy, false otherwise
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * API client object for convenient access to all endpoints
 */
export const walletApi = {
  getScore: getWalletScore,
  getHistory: getWalletHistory,
  compare: compareWallets,
  extractWallet,
  getExtractionStatus,
  getExtractionStatusByAddress,
  checkHealth: checkApiHealth,
  baseUrl: API_BASE_URL,
};

export default walletApi;
