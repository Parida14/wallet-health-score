'use client';

import { Activity, PieChart, AlertTriangle, TrendingUp, Shield } from 'lucide-react';
import type { ScoreComponents, ComponentKey } from '@/types/wallet';
import { COMPONENT_META, componentToPercent } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ComponentBarsProps {
  components: ScoreComponents;
  className?: string;
  showDescriptions?: boolean;
  animated?: boolean;
}

const COMPONENT_ORDER: ComponentKey[] = [
  'activity',
  'diversification',
  'risk',
  'profitability',
  'stability',
];

const ICON_MAP = {
  Activity,
  PieChart,
  AlertTriangle,
  TrendingUp,
  Shield,
};

const COLOR_MAP: Record<ComponentKey, string> = {
  activity: 'bg-emerald-500',
  diversification: 'bg-indigo-500',
  risk: 'bg-amber-500',
  profitability: 'bg-purple-500',
  stability: 'bg-cyan-500',
};

const BG_COLOR_MAP: Record<ComponentKey, string> = {
  activity: 'bg-emerald-500/20',
  diversification: 'bg-indigo-500/20',
  risk: 'bg-amber-500/20',
  profitability: 'bg-purple-500/20',
  stability: 'bg-cyan-500/20',
};

/**
 * Horizontal bar chart showing all 5 score components with progress bars.
 */
export function ComponentBars({
  components,
  className,
  showDescriptions = false,
  animated = true,
}: ComponentBarsProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {COMPONENT_ORDER.map((key) => {
        const meta = COMPONENT_META[key];
        const value = componentToPercent(components[key]);
        const IconComponent = ICON_MAP[meta.icon as keyof typeof ICON_MAP];

        return (
          <div key={key} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={cn('p-1.5 rounded-md', BG_COLOR_MAP[key])}>
                  <IconComponent className="w-4 h-4" style={{ color: `var(--chart-${COMPONENT_ORDER.indexOf(key) + 1})` }} />
                </div>
                <span className="font-medium text-sm">{meta.label}</span>
              </div>
              <span className="text-sm font-semibold tabular-nums">
                {value}%
              </span>
            </div>
            
            {/* Progress bar */}
            <div className={cn('h-2 rounded-full overflow-hidden', BG_COLOR_MAP[key])}>
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-1000 ease-out',
                  COLOR_MAP[key]
                )}
                style={{
                  width: animated ? `${value}%` : '0%',
                  transitionDelay: animated ? `${COMPONENT_ORDER.indexOf(key) * 100}ms` : '0ms',
                }}
              />
            </div>
            
            {showDescriptions && (
              <p className="text-xs text-muted-foreground">
                {meta.description}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default ComponentBars;
