'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { WeeklyActivityPoint } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ActivityTrendChartProps {
  series: WeeklyActivityPoint[];
  className?: string;
}

interface ChartDataPoint {
  weekStart: string;
  weekEnd: string;
  label: string;
  txCount: number;
  activity: number;
}

const BAR_COLOR = '#6366f1'; // indigo-500
const LINE_COLOR = '#34d399'; // emerald-400

function formatWeekLabel(weekStart: string, compact: boolean): string {
  const d = new Date(weekStart + 'T00:00:00Z');
  if (compact) {
    return d.toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
  }
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

/**
 * Weekly on-chain activity: bars = tx count, line = activity intensity (0–100).
 */
export function ActivityTrendChart({ series, className }: ActivityTrendChartProps) {
  const data = useMemo<ChartDataPoint[]>(() => {
    return series.map((point) => ({
      weekStart: point.week_start,
      weekEnd: point.week_end,
      label: formatWeekLabel(point.week_start, series.length > 26),
      txCount: point.tx_count,
      activity: Math.round(point.activity_score * 100),
    }));
  }, [series]);

  const hasAnyTx = data.some((d) => d.txCount > 0);

  if (data.length === 0 || !hasAnyTx) {
    return (
      <div
        className={cn(
          'flex items-center justify-center h-[300px] text-muted-foreground text-sm text-center px-4',
          className
        )}
      >
        No transactions stored yet — run Fetch Wallet Data to build this trend.
      </div>
    );
  }

  // Show ~6–8 x-axis ticks so a 52-week chart stays readable
  const tickInterval = Math.max(0, Math.floor(data.length / 7) - 1);

  return (
    <div className={cn('w-full h-[300px]', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.15)"
            strokeOpacity={0.7}
            vertical={false}
          />
          <XAxis
            dataKey="label"
            stroke="rgba(255,255,255,0.6)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            dy={8}
            interval={tickInterval}
          />
          <YAxis
            yAxisId="count"
            stroke="rgba(255,255,255,0.6)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={36}
            allowDecimals={false}
          />
          <YAxis
            yAxisId="score"
            orientation="right"
            domain={[0, 100]}
            stroke="rgba(255,255,255,0.6)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={36}
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as ChartDataPoint;
              const start = new Date(point.weekStart + 'T00:00:00Z').toLocaleDateString(
                'en-US',
                { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }
              );
              const end = new Date(point.weekEnd + 'T00:00:00Z').toLocaleDateString(
                'en-US',
                { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }
              );
              return (
                <div className="bg-popover border border-border rounded-lg px-4 py-3 shadow-lg">
                  <p className="text-xs text-muted-foreground mb-2">
                    {start} – {end}
                  </p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    <span className="text-muted-foreground">Transactions</span>
                    <span className="font-medium text-right">{point.txCount}</span>
                    <span className="text-muted-foreground">Activity intensity</span>
                    <span className="font-medium text-right" style={{ color: LINE_COLOR }}>
                      {point.activity}
                    </span>
                  </div>
                </div>
              );
            }}
          />
          <Legend
            verticalAlign="top"
            height={28}
            formatter={(value) => (
              <span className="text-xs text-muted-foreground">{value}</span>
            )}
          />
          <Bar
            yAxisId="count"
            dataKey="txCount"
            name="Tx / week"
            fill={BAR_COLOR}
            fillOpacity={0.75}
            radius={[2, 2, 0, 0]}
            maxBarSize={18}
          />
          <Line
            yAxisId="score"
            type="monotone"
            dataKey="activity"
            name="Activity intensity"
            stroke={LINE_COLOR}
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, fill: LINE_COLOR, stroke: '#fff', strokeWidth: 2 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ActivityTrendChart;
