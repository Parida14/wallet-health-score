'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface LoadingCardProps {
  className?: string;
}

/**
 * Loading skeleton for the main score card.
 */
export function ScoreCardSkeleton({ className }: LoadingCardProps) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <Skeleton className="h-6 w-48 mb-2" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-7 w-7 rounded" />
              <Skeleton className="h-7 w-7 rounded" />
            </div>
          </div>
          <Skeleton className="h-5 w-24" />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Score gauge skeleton */}
        <div className="flex justify-center py-4">
          <Skeleton className="w-[180px] h-[180px] rounded-full" />
        </div>

        <Skeleton className="h-px w-full" />

        {/* Tabs skeleton */}
        <div>
          <Skeleton className="h-10 w-full mb-4" />
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-between">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-8 w-8 rounded" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-4 w-10" />
                </div>
                <Skeleton className="h-2 w-full rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Loading skeleton for the history chart.
 */
export function HistoryChartSkeleton({ className }: LoadingCardProps) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[300px] w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * Loading skeleton for the comparison table.
 */
export function ComparisonSkeleton({ className }: LoadingCardProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4 text-center">
              <Skeleton className="h-8 w-16 mx-auto mb-1" />
              <Skeleton className="h-3 w-20 mx-auto" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Wallet cards */}
      <div className="grid gap-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <Skeleton className="w-10 h-6" />
                <Skeleton className="w-[80px] h-[80px] rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-5 w-48 mb-2" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <div className="hidden md:flex gap-3">
                  {[...Array(5)].map((_, j) => (
                    <Skeleton key={j} className="h-4 w-16" />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/**
 * Full page loading state with animated gradient.
 */
export function PageLoadingState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-muted animate-pulse" />
        <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin" />
      </div>
      <p className="text-sm text-muted-foreground animate-pulse">
        Loading wallet data...
      </p>
    </div>
  );
}

/**
 * Error state component.
 */
export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-destructive/50 bg-destructive/5">
      <CardContent className="py-8 text-center">
        <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">⚠️</span>
        </div>
        <h3 className="font-semibold text-lg mb-2">{title}</h3>
        {message && (
          <p className="text-sm text-muted-foreground mb-4">{message}</p>
        )}
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm text-primary hover:underline"
          >
            Try again
          </button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Empty state component for when no data is found.
 */
export function EmptyState({
  title = 'No data found',
  message,
  action,
}: {
  title?: string;
  message?: string;
  action?: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">🔍</span>
        </div>
        <h3 className="font-semibold text-lg mb-2">{title}</h3>
        {message && (
          <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
            {message}
          </p>
        )}
        {action}
      </CardContent>
    </Card>
  );
}
