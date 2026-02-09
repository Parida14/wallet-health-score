'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import type { WalletScore } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface HistoryChartProps {
  history: WalletScore[];
  className?: string;
  showGrid?: boolean;
  variant?: 'line' | 'area';
}

interface ChartDataPoint {
  date: string;
  displayDate: string;
  score: number;
  activity: number;
  diversification: number;
  risk: number;
  profitability: number;
  stability: number;
}

/**
 * Line/Area chart showing historical wallet scores over time.
 */
export function HistoryChart({
  history,
  className,
  showGrid = true,
  variant = 'area',
}: HistoryChartProps) {
  const data = useMemo<ChartDataPoint[]>(() => {
    // History comes in reverse chronological order, so we reverse it for the chart
    return [...history].reverse().map((entry) => {
      const date = new Date(entry.last_updated);
      return {
        date: entry.last_updated,
        displayDate: date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        score: Math.round(entry.wallet_score * 100),
        activity: Math.round(entry.components.activity * 100),
        diversification: Math.round(entry.components.diversification * 100),
        risk: Math.round(entry.components.risk * 100),
        profitability: Math.round(entry.components.profitability * 100),
        stability: Math.round(entry.components.stability * 100),
      };
    });
  }, [history]);

  if (data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-[300px] text-muted-foreground', className)}>
        No historical data available
      </div>
    );
  }

  const ChartComponent = variant === 'area' ? AreaChart : LineChart;

  return (
    <div className={cn('w-full h-[300px]', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <ChartComponent data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
              strokeOpacity={0.5}
              vertical={false}
            />
          )}
          <XAxis
            dataKey="displayDate"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            dy={10}
          />
          <YAxis
            domain={[0, 100]}
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}`}
            width={35}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as ChartDataPoint;
              return (
                <div className="bg-popover border border-border rounded-lg px-4 py-3 shadow-lg">
                  <p className="text-xs text-muted-foreground mb-2">{label}</p>
                  <p className="text-2xl font-bold text-primary mb-2">
                    {point.score}
                  </p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    <span className="text-muted-foreground">Activity</span>
                    <span className="font-medium text-right">{point.activity}%</span>
                    <span className="text-muted-foreground">Diversification</span>
                    <span className="font-medium text-right">{point.diversification}%</span>
                    <span className="text-muted-foreground">Risk</span>
                    <span className="font-medium text-right">{point.risk}%</span>
                    <span className="text-muted-foreground">Profitability</span>
                    <span className="font-medium text-right">{point.profitability}%</span>
                    <span className="text-muted-foreground">Stability</span>
                    <span className="font-medium text-right">{point.stability}%</span>
                  </div>
                </div>
              );
            }}
          />
          {variant === 'area' ? (
            <>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="score"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fill="url(#scoreGradient)"
                dot={false}
                activeDot={{
                  r: 6,
                  fill: 'hsl(var(--primary))',
                  stroke: 'hsl(var(--background))',
                  strokeWidth: 2,
                }}
              />
            </>
          ) : (
            <Line
              type="monotone"
              dataKey="score"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 6,
                fill: 'hsl(var(--primary))',
                stroke: 'hsl(var(--background))',
                strokeWidth: 2,
              }}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}

export default HistoryChart;
