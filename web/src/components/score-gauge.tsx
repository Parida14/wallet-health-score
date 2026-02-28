'use client';

import { useMemo } from 'react';
import { getScoreCategory, type ScoreCategory } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ScoreGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}

const SIZE_CONFIG = {
  sm: { width: 120, strokeWidth: 8, fontSize: 'text-2xl', labelSize: 'text-xs' },
  md: { width: 180, strokeWidth: 10, fontSize: 'text-4xl', labelSize: 'text-sm' },
  lg: { width: 240, strokeWidth: 12, fontSize: 'text-5xl', labelSize: 'text-base' },
};

const CATEGORY_COLORS: Record<ScoreCategory, { stroke: string; glow: string }> = {
  excellent: { stroke: '#22c55e', glow: 'rgba(34, 197, 94, 0.4)' },
  good: { stroke: '#4ade80', glow: 'rgba(74, 222, 128, 0.3)' },
  fair: { stroke: '#facc15', glow: 'rgba(250, 204, 21, 0.3)' },
  poor: { stroke: '#f97316', glow: 'rgba(249, 115, 22, 0.3)' },
  critical: { stroke: '#ef4444', glow: 'rgba(239, 68, 68, 0.3)' },
};

/**
 * Circular gauge component for displaying wallet health scores.
 * Shows a score from 0-100 with color-coded categories.
 */
export function ScoreGauge({
  score,
  size = 'md',
  showLabel = true,
  animated = true,
  className,
}: ScoreGaugeProps) {
  const config = SIZE_CONFIG[size];
  const category = getScoreCategory(score);
  const colors = CATEGORY_COLORS[category];
  
  const { circumference, dashOffset, center, radius } = useMemo(() => {
    const r = (config.width - config.strokeWidth) / 2;
    const c = 2 * Math.PI * r;
    // Score is 0-100, we want to fill proportionally
    const normalizedScore = Math.max(0, Math.min(100, score));
    const offset = c - (normalizedScore / 100) * c;
    return {
      circumference: c,
      dashOffset: offset,
      center: config.width / 2,
      radius: r,
    };
  }, [score, config]);

  const categoryLabel = useMemo(() => {
    const labels: Record<ScoreCategory, string> = {
      excellent: 'Excellent',
      good: 'Good',
      fair: 'Fair',
      poor: 'Poor',
      critical: 'Critical',
    };
    return labels[category];
  }, [category]);

  return (
    <div className={cn('relative inline-flex flex-col items-center', className)}>
      <svg
        width={config.width}
        height={config.width}
        viewBox={`0 0 ${config.width} ${config.width}`}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={config.strokeWidth}
          className="text-muted/30"
        />
        
        {/* Glow effect */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={config.strokeWidth + 4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{
            filter: `drop-shadow(0 0 8px ${colors.glow})`,
            opacity: 0.5,
          }}
          className={animated ? 'animate-score-fill' : ''}
        />
        
        {/* Score arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={config.strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{
            transition: animated ? 'stroke-dashoffset 1.5s ease-out' : 'none',
          }}
          className={animated ? 'animate-score-fill' : ''}
        />
      </svg>
      
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={cn(
            config.fontSize,
            'font-bold tabular-nums tracking-tight'
          )}
          style={{ color: colors.stroke }}
        >
          {Math.round(score)}
        </span>
        {showLabel && (
          <span
            className={cn(
              config.labelSize,
              'font-medium text-muted-foreground mt-1'
            )}
          >
            {categoryLabel}
          </span>
        )}
      </div>
    </div>
  );
}

export default ScoreGauge;
