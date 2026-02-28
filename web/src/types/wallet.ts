/**
 * Type definitions for wallet health score data models.
 * These interfaces match the FastAPI backend response schemas.
 */

/**
 * Individual score components (0-1 scale)
 */
export interface ScoreComponents {
  activity: number;
  diversification: number;
  risk: number;
  profitability: number;
  stability: number;
}

/**
 * Metrics data from the scoring engine
 */
export interface WalletMetrics {
  transactions_count: number;
  recent_transactions_count: number;
  positions_count: number;
}

/**
 * Complete wallet score response from the API
 */
export interface WalletScore {
  address: string;
  wallet_score: number;
  components: ScoreComponents;
  last_updated: string;
  metrics: WalletMetrics;
}

/**
 * Comparison statistics returned by the compare endpoint
 */
export interface ComparisonStats {
  total_wallets_found: number;
  missing_wallets: string[];
  average_score: number;
  highest_score: number;
  lowest_score: number;
  ranking: Array<{
    address: string;
    score: number;
  }>;
}

/**
 * Response from the /compare endpoint
 */
export interface CompareResponse {
  wallets: WalletScore[];
  comparison: ComparisonStats;
}

/**
 * Request body for the /compare endpoint
 */
export interface CompareRequest {
  addresses: string[];
}

/**
 * Extraction job status type
 */
export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Extraction job response from the API
 */
export interface ExtractionJob {
  id: string;
  address: string;
  status: ExtractionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Score category based on the total score value
 */
export type ScoreCategory = 'excellent' | 'good' | 'fair' | 'poor' | 'critical';

/**
 * Component key type for type-safe component access
 */
export type ComponentKey = keyof ScoreComponents;

/**
 * Component display metadata
 */
export interface ComponentMeta {
  key: ComponentKey;
  label: string;
  description: string;
  icon: string;
}

/**
 * All component metadata for display purposes
 */
export const COMPONENT_META: Record<ComponentKey, ComponentMeta> = {
  activity: {
    key: 'activity',
    label: 'Activity',
    description: 'Transaction frequency and engagement',
    icon: 'Activity',
  },
  diversification: {
    key: 'diversification',
    label: 'Diversification',
    description: 'Portfolio spread across tokens and protocols',
    icon: 'PieChart',
  },
  risk: {
    key: 'risk',
    label: 'Risk',
    description: 'Exposure to volatile assets and leverage',
    icon: 'AlertTriangle',
  },
  profitability: {
    key: 'profitability',
    label: 'Profitability',
    description: 'Realized and unrealized gains and losses',
    icon: 'TrendingUp',
  },
  stability: {
    key: 'stability',
    label: 'Stability',
    description: 'Holding patterns and asset rotation',
    icon: 'Shield',
  },
};

/**
 * Get the score category based on the score value (0-100)
 */
export function getScoreCategory(score: number): ScoreCategory {
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'good';
  if (score >= 40) return 'fair';
  if (score >= 20) return 'poor';
  return 'critical';
}

/**
 * Format wallet address for display (truncated)
 */
export function formatAddress(address: string, chars: number = 6): string {
  if (address.length <= chars * 2 + 2) return address;
  return `${address.slice(0, chars + 2)}...${address.slice(-chars)}`;
}

/**
 * Validate Ethereum address format
 */
export function isValidEthereumAddress(address: string): boolean {
  return /^0x[a-fA-F0-9]{40}$/.test(address);
}

/**
 * Convert component score (0-1) to percentage (0-100)
 */
export function componentToPercent(value: number): number {
  return Math.round(value * 100);
}

/**
 * Well-known Ethereum addresses for testing and examples
 */
export const SAMPLE_WALLETS = [
  {
    address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    label: 'vitalik.eth',
    description: 'Vitalik Buterin',
  },
  {
    address: '0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe',
    label: 'Ethereum Foundation',
    description: 'Ethereum Foundation Multisig',
  },
  {
    address: '0x1a9C8182C09F50C8318d769245beA52c32BE35BC',
    label: 'Uniswap Treasury',
    description: 'Uniswap Protocol Treasury',
  },
  {
    address: '0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503',
    label: 'Binance Hot Wallet',
    description: 'Binance Exchange Hot Wallet',
  },
  {
    address: '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
    label: 'Binance Cold Wallet',
    description: 'Binance Exchange Cold Storage',
  },
] as const;
