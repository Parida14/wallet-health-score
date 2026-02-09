'use client';

import { useState, useCallback, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Loader2, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { isValidEthereumAddress } from '@/types/wallet';
import { cn } from '@/lib/utils';

interface WalletSearchProps {
  className?: string;
  placeholder?: string;
  defaultValue?: string;
  onSearch?: (address: string) => void;
  autoFocus?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Search input component for looking up wallet addresses.
 * Validates Ethereum addresses and navigates to the wallet detail page.
 */
export function WalletSearch({
  className,
  placeholder = 'Enter wallet address (0x...)',
  defaultValue = '',
  onSearch,
  autoFocus = false,
  size = 'md',
}: WalletSearchProps) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      
      const trimmedValue = value.trim();
      
      if (!trimmedValue) {
        setError('Please enter a wallet address');
        return;
      }

      if (!isValidEthereumAddress(trimmedValue)) {
        setError('Invalid Ethereum address format');
        return;
      }

      setError(null);
      setIsLoading(true);

      try {
        if (onSearch) {
          onSearch(trimmedValue);
        } else {
          router.push(`/wallet/${trimmedValue}`);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [value, onSearch, router]
  );

  const handleClear = useCallback(() => {
    setValue('');
    setError(null);
  }, []);

  const sizeClasses = {
    sm: 'h-9 text-sm',
    md: 'h-11 text-base',
    lg: 'h-14 text-lg',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <form onSubmit={handleSubmit} className={cn('w-full', className)}>
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
          <Search className={iconSizes[size]} />
        </div>
        <Input
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (error) setError(null);
          }}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className={cn(
            sizeClasses[size],
            'pl-10 pr-24 font-mono-address',
            error && 'border-destructive focus-visible:ring-destructive'
          )}
        />
        <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {value && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleClear}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
          <Button
            type="submit"
            disabled={isLoading || !value.trim()}
            size={size === 'lg' ? 'default' : 'sm'}
            className="h-8"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              'Search'
            )}
          </Button>
        </div>
      </div>
      {error && (
        <p className="text-sm text-destructive mt-2 animate-in fade-in slide-in-from-top-1">
          {error}
        </p>
      )}
    </form>
  );
}

export default WalletSearch;
