'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScoreCard } from '@/components/score-card';
import { HistoryChart } from '@/components/history-chart';
import { WalletSearch } from '@/components/wallet-search';
import {
  ScoreCardSkeleton,
  HistoryChartSkeleton,
  ErrorState,
  EmptyState,
} from '@/components/loading-states';
import { walletApi, ApiError } from '@/lib/api';
import type { WalletScore } from '@/types/wallet';
import { formatAddress } from '@/types/wallet';

/**
 * Wallet detail page showing score, history, and metrics.
 */
export default function WalletDetailPage() {
  const params = useParams();
  const address = params.address as string;

  const [score, setScore] = useState<WalletScore | null>(null);
  const [history, setHistory] = useState<WalletScore[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      // Fetch score and history in parallel
      const [scoreData, historyData] = await Promise.all([
        walletApi.getScore(address),
        walletApi.getHistory(address, 30).catch(() => []), // History is optional
      ]);

      setScore(scoreData);
      setHistory(historyData);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) {
          setError('Wallet not found. This address may not have been indexed yet.');
        } else {
          setError(err.detail || err.message);
        }
      } else {
        setError('Failed to fetch wallet data. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await fetchData();
    setIsRefreshing(false);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Wallet Analysis</h1>
            <p className="text-sm text-muted-foreground font-mono-address">
              {formatAddress(address, 10)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <div className="mb-8">
        <WalletSearch defaultValue={address} />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid lg:grid-cols-2 gap-6">
          <ScoreCardSkeleton />
          <HistoryChartSkeleton />
        </div>
      ) : error ? (
        <ErrorState
          title="Unable to Load Wallet"
          message={error}
          onRetry={fetchData}
        />
      ) : !score ? (
        <EmptyState
          title="Wallet Not Found"
          message="This wallet address hasn't been indexed yet. Try one of our sample wallets or check back later."
          action={
            <Link href="/">
              <Button variant="outline">Browse Sample Wallets</Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Score Card */}
            <ScoreCard data={score} />

            {/* History Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Score History</CardTitle>
              </CardHeader>
              <CardContent>
                {history.length > 0 ? (
                  <Tabs defaultValue="30d">
                    <TabsList className="mb-4">
                      <TabsTrigger value="7d">7 Days</TabsTrigger>
                      <TabsTrigger value="30d">30 Days</TabsTrigger>
                    </TabsList>
                    <TabsContent value="7d">
                      <HistoryChart history={history.slice(0, 7)} />
                    </TabsContent>
                    <TabsContent value="30d">
                      <HistoryChart history={history} />
                    </TabsContent>
                  </Tabs>
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                    <p>No historical data available yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Additional Info */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <a
                  href={`https://etherscan.io/address/${address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="sm">
                    View on Etherscan
                  </Button>
                </a>
                <a
                  href={`https://debank.com/profile/${address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="sm">
                    View on DeBank
                  </Button>
                </a>
                <Link href={`/compare?addresses=${address}`}>
                  <Button variant="outline" size="sm">
                    Compare with Others
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
