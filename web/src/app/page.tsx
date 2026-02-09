import Link from 'next/link';
import { ArrowRight, Sparkles, Shield, TrendingUp, PieChart, Activity } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { WalletSearch } from '@/components/wallet-search';
import { SAMPLE_WALLETS, formatAddress } from '@/types/wallet';

/**
 * Home page with search functionality and featured wallets.
 */
export default function HomePage() {
  return (
    <div className="relative">
      {/* Background gradient mesh */}
      <div className="absolute inset-0 gradient-mesh pointer-events-none" />
      
      <div className="relative container mx-auto px-4 py-12">
        {/* Hero Section */}
        <section className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="secondary" className="mb-4">
            <Sparkles className="w-3 h-3 mr-1" />
            On-Chain Analytics
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
            Understand Your{' '}
            <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
              Wallet Health
            </span>
          </h1>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Get a comprehensive health score for any Ethereum wallet based on activity,
            diversification, risk exposure, profitability, and stability metrics.
          </p>

          {/* Search */}
          <div className="max-w-xl mx-auto">
            <WalletSearch size="lg" autoFocus />
          </div>
        </section>

        {/* Features Grid */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-center mb-8">
            Five Dimensions of Wallet Health
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <FeatureCard
              icon={<Activity className="w-5 h-5" />}
              title="Activity"
              description="Transaction frequency and engagement patterns"
              color="text-emerald-500"
              bgColor="bg-emerald-500/10"
            />
            <FeatureCard
              icon={<PieChart className="w-5 h-5" />}
              title="Diversification"
              description="Portfolio spread across tokens and protocols"
              color="text-indigo-500"
              bgColor="bg-indigo-500/10"
            />
            <FeatureCard
              icon={<Shield className="w-5 h-5" />}
              title="Risk"
              description="Exposure to volatile assets and leverage"
              color="text-amber-500"
              bgColor="bg-amber-500/10"
            />
            <FeatureCard
              icon={<TrendingUp className="w-5 h-5" />}
              title="Profitability"
              description="Realized and unrealized gains and losses"
              color="text-purple-500"
              bgColor="bg-purple-500/10"
            />
            <FeatureCard
              icon={<Sparkles className="w-5 h-5" />}
              title="Stability"
              description="Holding patterns and asset rotation"
              color="text-cyan-500"
              bgColor="bg-cyan-500/10"
            />
          </div>
        </section>

        {/* Sample Wallets */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">Try These Wallets</h2>
            <Link href="/compare">
              <Button variant="outline" size="sm">
                Compare Wallets
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {SAMPLE_WALLETS.slice(0, 6).map((wallet) => (
              <Link key={wallet.address} href={`/wallet/${wallet.address}`}>
                <Card className="h-full hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all cursor-pointer group">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold group-hover:text-primary transition-colors">
                          {wallet.label}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {wallet.description}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    <code className="text-xs font-mono-address text-muted-foreground bg-muted px-2 py-1 rounded block truncate">
                      {formatAddress(wallet.address, 10)}
                    </code>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="mt-16 text-center">
          <h2 className="text-2xl font-semibold mb-8">How It Works</h2>
          <div className="grid sm:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <StepCard
              step={1}
              title="Enter Address"
              description="Paste any Ethereum wallet address to analyze"
            />
            <StepCard
              step={2}
              title="Analyze Data"
              description="We fetch transaction history and token balances"
            />
            <StepCard
              step={3}
              title="Get Score"
              description="View your health score with detailed breakdown"
            />
          </div>
        </section>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  color,
  bgColor,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  bgColor: string;
}) {
  return (
    <Card className="text-center hover:shadow-md transition-shadow">
      <CardContent className="pt-6 pb-4">
        <div className={`w-12 h-12 rounded-xl ${bgColor} flex items-center justify-center mx-auto mb-3`}>
          <span className={color}>{icon}</span>
        </div>
        <h3 className="font-semibold mb-1">{title}</h3>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function StepCard({
  step,
  title,
  description,
}: {
  step: number;
  title: string;
  description: string;
}) {
  return (
    <div className="relative">
      <div className="w-10 h-10 rounded-full bg-primary/10 border-2 border-primary flex items-center justify-center mx-auto mb-4">
        <span className="font-bold text-primary">{step}</span>
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
