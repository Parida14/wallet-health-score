'use client';

import { ExternalLink, Copy, Check } from 'lucide-react';
import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScoreGauge } from '@/components/score-gauge';
import { ComponentBars } from '@/components/component-bars';
import { ComponentRadar } from '@/components/component-radar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { WalletScore } from '@/types/wallet';
import { formatAddress, getScoreCategory } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ScoreCardProps {
  data: WalletScore;
  className?: string;
  showMetrics?: boolean;
  variant?: 'full' | 'compact';
}

/**
 * Complete score card component displaying wallet health score,
 * component breakdown, and optional metrics.
 */
export function ScoreCard({
  data,
  className,
  showMetrics = true,
  variant = 'full',
}: ScoreCardProps) {
  const [copied, setCopied] = useState(false);
  const category = getScoreCategory(data.wallet_score * 100);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(data.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [data.address]);

  const etherscanUrl = `https://etherscan.io/address/${data.address}`;
  const lastUpdated = new Date(data.last_updated).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  if (variant === 'compact') {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <ScoreGauge score={data.wallet_score * 100} size="sm" showLabel={false} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono-address text-sm truncate">
                  {formatAddress(data.address)}
                </span>
                <Badge variant="secondary" className="text-xs capitalize">
                  {category}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Updated {lastUpdated}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold mb-2">
              Wallet Health Score
            </CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              <code className="font-mono-address text-sm bg-muted px-2 py-1 rounded">
                {formatAddress(data.address, 8)}
              </code>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                asChild
              >
                <a href={etherscanUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </Button>
            </div>
          </div>
          <Badge variant="outline" className="text-xs">
            {lastUpdated}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main score display */}
        <div className="flex flex-col items-center py-4">
          <ScoreGauge score={data.wallet_score * 100} size="lg" />
        </div>

        <Separator />

        {/* Component breakdown */}
        <Tabs defaultValue="bars" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="bars">Breakdown</TabsTrigger>
            <TabsTrigger value="radar">Radar</TabsTrigger>
          </TabsList>
          <TabsContent value="bars" className="mt-4">
            <ComponentBars components={data.components} showDescriptions />
          </TabsContent>
          <TabsContent value="radar" className="mt-4">
            <ComponentRadar components={data.components} />
          </TabsContent>
        </Tabs>

        {/* Metrics */}
        {showMetrics && data.metrics && (
          <>
            <Separator />
            <div>
              <h4 className="text-sm font-semibold mb-3">Wallet Metrics</h4>
              <div className="grid grid-cols-3 gap-4">
                <MetricItem
                  label="Total Transactions"
                  value={data.metrics.transactions_count}
                />
                <MetricItem
                  label="Recent (30d)"
                  value={data.metrics.recent_transactions_count}
                />
                <MetricItem
                  label="Token Positions"
                  value={data.metrics.positions_count}
                />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function MetricItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-bold tabular-nums">{value.toLocaleString()}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

export default ScoreCard;
