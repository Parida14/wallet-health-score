'use client';

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { ScoreComponents, ComponentKey } from '@/types/wallet';
import { COMPONENT_META, componentToPercent } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface ComponentRadarProps {
  components: ScoreComponents;
  className?: string;
  showLabels?: boolean;
  fillOpacity?: number;
}

interface RadarDataPoint {
  component: string;
  value: number;
  fullMark: number;
  key: ComponentKey;
}

const COMPONENT_ORDER: ComponentKey[] = [
  'activity',
  'diversification',
  'risk',
  'profitability',
  'stability',
];

/** Bright radar colors for dark mode visibility */
const RADAR_STROKE = '#22d3ee'; // Cyan-400
const RADAR_FILL = '#06b6d4';  // Cyan-500
const GRID_COLOR = 'rgba(255,255,255,0.18)';
const LABEL_COLOR = 'rgba(255,255,255,0.85)';

/**
 * Radar chart component for visualizing the 5 score components.
 * Shows a pentagon shape with each vertex representing a component.
 */
export function ComponentRadar({
  components,
  className,
  showLabels = true,
  fillOpacity = 0.45,
}: ComponentRadarProps) {
  const data: RadarDataPoint[] = COMPONENT_ORDER.map((key) => ({
    component: COMPONENT_META[key].label,
    value: componentToPercent(components[key]),
    fullMark: 100,
    key,
  }));

  return (
    <div className={cn('w-full h-[300px]', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid
            stroke={GRID_COLOR}
            strokeOpacity={0.7}
          />
          {showLabels && (
            <PolarAngleAxis
              dataKey="component"
              tick={{
                fill: LABEL_COLOR,
                fontSize: 12,
                fontWeight: 600,
              }}
              tickLine={false}
            />
          )}
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Score"
            dataKey="value"
            stroke={RADAR_STROKE}
            fill={RADAR_FILL}
            fillOpacity={fillOpacity}
            strokeWidth={2.5}
            dot={{
              r: 5,
              fill: RADAR_STROKE,
              stroke: '#fff',
              strokeWidth: 1,
            }}
            activeDot={{
              r: 7,
              fill: RADAR_STROKE,
              stroke: '#fff',
              strokeWidth: 2,
            }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as RadarDataPoint;
              const meta = COMPONENT_META[point.key];
              return (
                <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-lg">
                  <p className="font-semibold text-sm text-foreground">{meta.label}</p>
                  <p className="text-2xl font-bold" style={{ color: RADAR_STROKE }}>
                    {point.value}%
                  </p>
                  <p className="text-xs text-muted-foreground mt-1 max-w-[180px]">
                    {meta.description}
                  </p>
                </div>
              );
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ComponentRadar;
