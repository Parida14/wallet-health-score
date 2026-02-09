'use client';

import { useState, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Plus, X, GitCompare, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ComparisonTable } from '@/components/comparison-table';
import { ComparisonSkeleton, ErrorState, EmptyState } from '@/components/loading-states';
import { walletApi, ApiError } from '@/lib/api';
import type { CompareResponse } from '@/types/wallet';
import { isValidEthereumAddress, formatAddress, SAMPLE_WALLETS } from '@/types/wallet';
import { cn } from '@/lib/utils';

/**
 * Compare page content component (uses useSearchParams)
 */
function ComparePageContent() {
  const searchParams = useSearchParams();
  const initialAddresses = searchParams.get('addresses')?.split(',').filter(Boolean) || [];

  const [addresses, setAddresses] = useState<string[]>(
    initialAddresses.length > 0 ? initialAddresses : []
  );
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddAddress = useCallback(() => {
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setInputError('Please enter a wallet address');
      return;
    }

    if (!isValidEthereumAddress(trimmed)) {
      setInputError('Invalid Ethereum address format');
      return;
    }

    if (addresses.includes(trimmed.toLowerCase())) {
      setInputError('This address is already in the list');
      return;
    }

    if (addresses.length >= 10) {
      setInputError('Maximum 10 addresses allowed');
      return;
    }

    setAddresses((prev) => [...prev, trimmed]);
    setInputValue('');
    setInputError(null);
  }, [inputValue, addresses]);

  const handleRemoveAddress = useCallback((address: string) => {
    setAddresses((prev) => prev.filter((a) => a.toLowerCase() !== address.toLowerCase()));
  }, []);

  const handleAddSample = useCallback((address: string) => {
    if (!addresses.includes(address.toLowerCase()) && addresses.length < 10) {
      setAddresses((prev) => [...prev, address]);
    }
  }, [addresses]);

  const handleCompare = useCallback(async () => {
    if (addresses.length < 2) {
      setError('Please add at least 2 wallet addresses to compare');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await walletApi.compare(addresses);
      setComparison(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('Failed to compare wallets. Please try again.');
      }
      setComparison(null);
    } finally {
      setIsLoading(false);
    }
  }, [addresses]);

  const handleClear = useCallback(() => {
    setAddresses([]);
    setComparison(null);
    setError(null);
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Link href="/">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Compare Wallets</h1>
          <p className="text-sm text-muted-foreground">
            Compare health scores across multiple wallets
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Add Wallets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Input */}
              <div className="flex gap-2">
                <Input
                  value={inputValue}
                  onChange={(e) => {
                    setInputValue(e.target.value);
                    if (inputError) setInputError(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddAddress();
                    }
                  }}
                  placeholder="0x..."
                  className={cn(
                    'font-mono-address text-sm',
                    inputError && 'border-destructive'
                  )}
                />
                <Button onClick={handleAddAddress} size="icon">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {inputError && (
                <p className="text-sm text-destructive">{inputError}</p>
              )}

              {/* Address list */}
              {addresses.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">
                    Selected ({addresses.length}/10)
                  </p>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {addresses.map((addr) => (
                      <div
                        key={addr}
                        className="flex items-center justify-between bg-muted rounded-lg px-3 py-2"
                      >
                        <code className="text-xs font-mono-address truncate flex-1">
                          {formatAddress(addr, 8)}
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 ml-2"
                          onClick={() => handleRemoveAddress(addr)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={handleCompare}
                  disabled={addresses.length < 2 || isLoading}
                  className="flex-1"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <GitCompare className="w-4 h-4 mr-2" />
                  )}
                  Compare
                </Button>
                {addresses.length > 0 && (
                  <Button variant="outline" onClick={handleClear}>
                    Clear
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Sample wallets */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Add</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_WALLETS.map((wallet) => (
                  <Badge
                    key={wallet.address}
                    variant="outline"
                    className={cn(
                      'cursor-pointer hover:bg-accent transition-colors',
                      addresses.includes(wallet.address) && 'bg-accent'
                    )}
                    onClick={() => handleAddSample(wallet.address)}
                  >
                    {wallet.label}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          {isLoading ? (
            <ComparisonSkeleton />
          ) : error ? (
            <ErrorState
              title="Comparison Failed"
              message={error}
              onRetry={handleCompare}
            />
          ) : comparison ? (
            <ComparisonTable data={comparison} />
          ) : (
            <EmptyState
              title="No Comparison Yet"
              message="Add at least 2 wallet addresses and click Compare to see the results."
              action={
                addresses.length < 2 ? (
                  <p className="text-sm text-muted-foreground">
                    {addresses.length === 0
                      ? 'Start by adding wallet addresses'
                      : 'Add one more wallet to compare'}
                  </p>
                ) : (
                  <Button onClick={handleCompare}>
                    <GitCompare className="w-4 h-4 mr-2" />
                    Compare Now
                  </Button>
                )
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Compare page with Suspense boundary for useSearchParams
 */
export default function ComparePage() {
  return (
    <Suspense fallback={<ComparePageLoading />}>
      <ComparePageContent />
    </Suspense>
  );
}

function ComparePageLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-10 h-10 rounded bg-muted animate-pulse" />
        <div>
          <div className="h-8 w-48 bg-muted rounded animate-pulse mb-2" />
          <div className="h-4 w-64 bg-muted rounded animate-pulse" />
        </div>
      </div>
      <ComparisonSkeleton />
    </div>
  );
}
