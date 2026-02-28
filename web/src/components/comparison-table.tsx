'use client';

import { Trophy, Medal, Award } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScoreGauge } from '@/components/score-gauge';
import type { CompareResponse } from '@/types/wallet';
import { formatAddress, getScoreCategory, componentToPercent } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ComparisonTableProps {
  data: CompareResponse;
  className?: string;
}

const RANK_ICONS = [Trophy, Medal, Award];
const RANK_COLORS = ['text-yellow-500', 'text-gray-400', 'text-amber-600'];

/**
 * Table component for comparing multiple wallets side by side.
 */
export function ComparisonTable({ data, className }: ComparisonTableProps) {
  const { wallets, comparison } = data;

  // Sort wallets by score descending
  const sortedWallets = [...wallets].sort(
    (a, b) => b.wallet_score - a.wallet_score
  );

  return (
    <div className={cn('space-y-6', className)}>
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Wallets Found"
          value={comparison.total_wallets_found}
        />
        <StatCard
          label="Average Score"
          value={Math.round(comparison.average_score * 100)}
          suffix="%"
        />
        <StatCard
          label="Highest Score"
          value={Math.round(comparison.highest_score * 100)}
          suffix="%"
          highlight="success"
        />
        <StatCard
          label="Lowest Score"
          value={Math.round(comparison.lowest_score * 100)}
          suffix="%"
          highlight="warning"
        />
      </div>

      {/* Missing wallets warning */}
      {comparison.missing_wallets.length > 0 && (
        <Card className="border-amber-500/50 bg-amber-500/10">
          <CardContent className="py-3">
            <p className="text-sm text-amber-600 dark:text-amber-400">
              <strong>Note:</strong> {comparison.missing_wallets.length} wallet(s) not found:{' '}
              {comparison.missing_wallets.map((addr) => formatAddress(addr)).join(', ')}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Wallet comparison cards */}
      <div className="grid gap-4">
        {sortedWallets.map((wallet, index) => {
          const RankIcon = RANK_ICONS[index] || null;
          const rankColor = RANK_COLORS[index] || 'text-muted-foreground';
          const category = getScoreCategory(wallet.wallet_score * 100);

          return (
            <Card
              key={wallet.address}
              className={cn(
                'transition-all hover:shadow-md',
                index === 0 && 'ring-2 ring-yellow-500/30'
              )}
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-10 text-center">
                    {RankIcon ? (
                      <RankIcon className={cn('w-6 h-6 mx-auto', rankColor)} />
                    ) : (
                      <span className="text-lg font-bold text-muted-foreground">
                        #{index + 1}
                      </span>
                    )}
                  </div>

                  {/* Score gauge */}
                  <ScoreGauge
                    score={wallet.wallet_score * 100}
                    size="sm"
                    showLabel={false}
                  />

                  {/* Wallet info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <code className="font-mono-address text-sm truncate">
                        {formatAddress(wallet.address, 8)}
                      </code>
                      <Badge variant="secondary" className="text-xs capitalize">
                        {category}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Score: {Math.round(wallet.wallet_score * 100)}
                    </p>
                  </div>

                  {/* Component scores */}
                  <div className="hidden md:flex gap-3 text-xs">
                    <ComponentPill
                      label="ACT"
                      value={componentToPercent(wallet.components.activity)}
                      color="bg-emerald-500"
                    />
                    <ComponentPill
                      label="DIV"
                      value={componentToPercent(wallet.components.diversification)}
                      color="bg-indigo-500"
                    />
                    <ComponentPill
                      label="RSK"
                      value={componentToPercent(wallet.components.risk)}
                      color="bg-amber-500"
                    />
                    <ComponentPill
                      label="PRF"
                      value={componentToPercent(wallet.components.profitability)}
                      color="bg-purple-500"
                    />
                    <ComponentPill
                      label="STB"
                      value={componentToPercent(wallet.components.stability)}
                      color="bg-cyan-500"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  suffix = '',
  highlight,
}: {
  label: string;
  value: number;
  suffix?: string;
  highlight?: 'success' | 'warning';
}) {
  return (
    <Card>
      <CardContent className="p-4 text-center">
        <p
          className={cn(
            'text-2xl font-bold tabular-nums',
            highlight === 'success' && 'text-green-500',
            highlight === 'warning' && 'text-amber-500'
          )}
        >
          {value}
          {suffix}
        </p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

function ComponentPill({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={cn('w-2 h-2 rounded-full', color)} />
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}%</span>
    </div>
  );
}

export default ComparisonTable;
