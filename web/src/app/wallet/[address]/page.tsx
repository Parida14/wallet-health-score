'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, Download, Loader2, CheckCircle2, XCircle, Info, Activity, PieChart, Shield, TrendingUp, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScoreCard } from '@/components/score-card';
import { HistoryChart } from '@/components/history-chart';
import { WalletSearch } from '@/components/wallet-search';
import {
  ScoreCardSkeleton,
  HistoryChartSkeleton,
  ErrorState,
} from '@/components/loading-states';
import { walletApi, ApiError } from '@/lib/api';
import type { WalletScore } from '@/types/wallet';
import type { ExtractionJob, ExtractionStatus } from '@/types/wallet';
import { formatAddress } from '@/types/wallet';

const POLL_INTERVAL_MS = 5000;

const STATUS_MESSAGES: Record<ExtractionStatus, string> = {
  pending: 'Queuing extraction job...',
  processing: 'Fetching transactions and calculating scores...',
  completed: 'Extraction complete! Loading your dashboard...',
  failed: 'Extraction failed.',
};

/**
 * Wallet detail page showing score, history, and metrics.
 * Supports on-demand extraction for wallets not yet indexed.
 */
export default function WalletDetailPage() {
  const params = useParams();
  const address = params.address as string;

  const [score, setScore] = useState<WalletScore | null>(null);
  const [history, setHistory] = useState<WalletScore[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isNotFound, setIsNotFound] = useState(false);

  // Extraction state
  const [extractionJob, setExtractionJob] = useState<ExtractionJob | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const fetchData = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);
    setIsNotFound(false);

    try {
      const [scoreData, historyData] = await Promise.all([
        walletApi.getScore(address),
        walletApi.getHistory(address, 30).catch(() => []),
      ]);

      setScore(scoreData);
      setHistory(historyData);
      // Clear extraction state on successful load
      setExtractionJob(null);
      setIsExtracting(false);
      setExtractionError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setIsNotFound(true);
      } else if (err instanceof ApiError) {
        setError(err.detail || err.message);
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

  // Poll extraction job status
  const startPolling = useCallback(
    (jobId: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const job = await walletApi.getExtractionStatus(jobId);
          setExtractionJob(job);

          if (job.status === 'completed') {
            stopPolling();
            // Reload the wallet data
            await fetchData();
          } else if (job.status === 'failed') {
            stopPolling();
            setIsExtracting(false);
            setExtractionError(job.error_message || 'Extraction failed. Please try again.');
          }
        } catch {
          // Polling error — keep trying
        }
      }, POLL_INTERVAL_MS);
    },
    [stopPolling, fetchData]
  );

  // Trigger extraction
  const handleExtract = useCallback(async () => {
    setIsExtracting(true);
    setExtractionError(null);
    setExtractionJob(null);

    try {
      const job = await walletApi.extractWallet(address);
      setExtractionJob(job);

      if (job.status === 'completed') {
        // Already done (unlikely but handle it)
        await fetchData();
      } else if (job.status === 'failed') {
        setIsExtracting(false);
        setExtractionError(job.error_message || 'Extraction failed.');
      } else {
        // pending or processing — start polling
        startPolling(job.id);
      }
    } catch (err) {
      setIsExtracting(false);
      if (err instanceof ApiError) {
        setExtractionError(err.detail || err.message);
      } else {
        setExtractionError('Failed to start extraction. Please try again.');
      }
    }
  }, [address, fetchData, startPolling]);

  // Re-extract (retry after failure)
  const handleRetryExtraction = useCallback(() => {
    setExtractionError(null);
    handleExtract();
  }, [handleExtract]);

  useEffect(() => {
    fetchData();
    return () => stopPolling();
  }, [fetchData, stopPolling]);

  const extractionStatus = extractionJob?.status as ExtractionStatus | undefined;

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
            disabled={isRefreshing || isExtracting}
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
      ) : isNotFound ? (
        /* Wallet not found — show extraction CTA */
        <ExtractionPanel
          address={address}
          isExtracting={isExtracting}
          extractionJob={extractionJob}
          extractionStatus={extractionStatus}
          extractionError={extractionError}
          onExtract={handleExtract}
          onRetry={handleRetryExtraction}
        />
      ) : score ? (
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

          {/* Scoring Methodology */}
          <ScoringMethodology />

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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExtract}
                  disabled={isExtracting}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isExtracting ? 'animate-spin' : ''}`} />
                  Re-extract Data
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

/**
 * Panel shown when a wallet has not been indexed yet.
 * Allows the user to trigger on-demand extraction.
 */
function ExtractionPanel({
  address,
  isExtracting,
  extractionJob,
  extractionStatus,
  extractionError,
  onExtract,
  onRetry,
}: {
  address: string;
  isExtracting: boolean;
  extractionJob: ExtractionJob | null;
  extractionStatus: ExtractionStatus | undefined;
  extractionError: string | null;
  onExtract: () => void;
  onRetry: () => void;
}) {
  // Not yet started extraction
  if (!isExtracting && !extractionError) {
    return (
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Download className="w-8 h-8 text-primary" />
          </div>
          <h3 className="font-semibold text-xl mb-2">Wallet Not Indexed Yet</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
            This Ethereum address hasn&apos;t been analyzed yet. Click below to fetch
            its transaction history, calculate health scores, and view the full dashboard.
          </p>
          <Button size="lg" onClick={onExtract}>
            <Download className="w-5 h-5 mr-2" />
            Fetch Wallet Data
          </Button>
          <p className="text-xs text-muted-foreground mt-4">
            This may take 30-60 seconds depending on transaction history size.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Extraction in progress
  if (isExtracting && !extractionError) {
    const statusMsg = extractionStatus
      ? STATUS_MESSAGES[extractionStatus]
      : 'Starting extraction...';

    return (
      <Card className="border-primary/30">
        <CardContent className="py-12 text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="w-16 h-16 rounded-full border-4 border-muted animate-pulse" />
            <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin" />
          </div>

          <h3 className="font-semibold text-xl mb-2">Extracting Wallet Data</h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
            {statusMsg}
          </p>

          {/* Progress steps */}
          <div className="max-w-xs mx-auto space-y-3 text-left">
            <ProgressStep
              label="Fetching transactions from blockchain"
              isActive={extractionStatus === 'pending' || extractionStatus === 'processing'}
              isComplete={extractionStatus === 'completed'}
            />
            <ProgressStep
              label="Analyzing token positions"
              isActive={extractionStatus === 'processing'}
              isComplete={extractionStatus === 'completed'}
            />
            <ProgressStep
              label="Calculating health scores"
              isActive={extractionStatus === 'processing'}
              isComplete={extractionStatus === 'completed'}
            />
          </div>

          <p className="text-xs text-muted-foreground mt-6">
            Please wait — this page will update automatically.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Extraction failed
  if (extractionError) {
    return (
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8 text-destructive" />
          </div>
          <h3 className="font-semibold text-xl mb-2">Extraction Failed</h3>
          <p className="text-sm text-muted-foreground mb-2 max-w-md mx-auto">
            We couldn&apos;t fetch data for this wallet. This might be due to API limits or
            a network issue.
          </p>
          {extractionError && (
            <p className="text-xs text-destructive/80 mb-6 max-w-md mx-auto font-mono">
              {extractionError}
            </p>
          )}
          <div className="flex items-center justify-center gap-3">
            <Button onClick={onRetry}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
            <Link href="/">
              <Button variant="outline">Browse Sample Wallets</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}

function ProgressStep({
  label,
  isActive,
  isComplete,
}: {
  label: string;
  isActive: boolean;
  isComplete: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      {isComplete ? (
        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
      ) : isActive ? (
        <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
      ) : (
        <div className="w-5 h-5 rounded-full border-2 border-muted shrink-0" />
      )}
      <span className={`text-sm ${isComplete ? 'text-emerald-400' : isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
        {label}
      </span>
    </div>
  );
}

const SCORING_COMPONENTS = [
  {
    icon: Activity,
    label: 'Activity',
    weight: '20%',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    description: 'Measures transaction frequency and engagement over the last 30 days.',
    details: 'Based on recent transaction count (60% weight) and unique smart contracts interacted with (40% weight). 10+ transactions and 5+ unique contracts yield maximum scores.',
  },
  {
    icon: PieChart,
    label: 'Diversification',
    weight: '20%',
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/10',
    description: 'Evaluates portfolio spread across different tokens.',
    details: 'Calculated from the number of unique ERC-20 tokens held with non-zero balances (70% weight) and a concentration factor (30% weight). Holding 10+ tokens scores highest.',
  },
  {
    icon: Shield,
    label: 'Risk',
    weight: '20%',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    description: 'Assesses exposure to volatile or risky assets. Higher score = safer.',
    details: 'Starts at a base of 50%, then adjusts: stablecoin holdings add up to +40%, meme/high-risk tokens subtract up to -30%, and large anomalous transactions subtract up to -20%.',
  },
  {
    icon: TrendingUp,
    label: 'Profitability',
    weight: '20%',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    description: 'Gauges trading activity patterns as a proxy for profitability.',
    details: 'Uses 90-day activity level (50% weight) and transaction frequency consistency (50% weight). Regular weekly activity and 50+ transactions in 90 days yield top scores.',
  },
  {
    icon: Sparkles,
    label: 'Stability',
    weight: '20%',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    description: 'Evaluates holding behavior and wallet maturity.',
    details: 'Combines stablecoin ratio (30% weight), wallet age — 2+ years for max score (40% weight), and low panic-sell indicators (30% weight).',
  },
] as const;

/**
 * Collapsible card explaining how the health score is calculated.
 */
function ScoringMethodology() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info className="w-5 h-5 text-muted-foreground" />
            <CardTitle>How the Score is Calculated</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Collapse' : 'Learn More'}
          </Button>
        </div>
        <CardDescription>
          The wallet health score (0-100) is a weighted average of five on-chain metrics, each scored 0-100 and weighted equally at 20%.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Formula */}
        <div className="bg-muted/50 rounded-lg px-4 py-3 mb-4 font-mono text-sm text-center">
          <span className="text-muted-foreground">Total Score = </span>
          <span className="text-emerald-400">0.2 &times; Activity</span>
          <span className="text-muted-foreground"> + </span>
          <span className="text-indigo-400">0.2 &times; Diversification</span>
          <span className="text-muted-foreground"> + </span>
          <span className="text-amber-400">0.2 &times; Risk</span>
          <span className="text-muted-foreground"> + </span>
          <span className="text-purple-400">0.2 &times; Profitability</span>
          <span className="text-muted-foreground"> + </span>
          <span className="text-cyan-400">0.2 &times; Stability</span>
        </div>

        {/* Component details */}
        <div className="grid gap-3">
          {SCORING_COMPONENTS.map((comp) => (
            <div
              key={comp.label}
              className="flex items-start gap-3 rounded-lg border border-border/50 p-3"
            >
              <div className={`p-2 rounded-lg ${comp.bgColor} shrink-0 mt-0.5`}>
                <comp.icon className={`w-4 h-4 ${comp.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">{comp.label}</span>
                  <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                    {comp.weight}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {comp.description}
                </p>
                {isExpanded && (
                  <p className="text-xs text-muted-foreground/80 mt-1.5 leading-relaxed border-t border-border/30 pt-1.5">
                    {comp.details}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {isExpanded && (
          <div className="mt-4 p-3 rounded-lg bg-muted/30 border border-border/30">
            <p className="text-xs text-muted-foreground leading-relaxed">
              <strong className="text-foreground">Data source:</strong> Transaction history and token balances are fetched from the Ethereum mainnet via the Alchemy API. Scores are recalculated on each extraction. The scoring model uses heuristic-based analysis and does not include price data for PnL calculations in the current version.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
