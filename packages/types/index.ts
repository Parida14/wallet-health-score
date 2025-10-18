export interface WalletScoreComponents {
  activity: number;
  diversification: number;
  risk: number;
  profitability: number;
  stability: number;
}

export interface WalletScoreResponse {
  address: string;
  wallet_score: number;
  components: WalletScoreComponents;
  last_updated: string;
}


