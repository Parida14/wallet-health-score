#!/bin/bash

# Vercel Pre-Deployment Checklist Script
# Run this script before deploying to Vercel to catch common issues

set -e

echo "🔍 Vercel Pre-Deployment Checklist"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in web directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: package.json not found${NC}"
    echo "   Run this script from the web/ directory"
    exit 1
fi

echo "✅ Found package.json"

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js version too old: $(node -v)${NC}"
    echo "   Vercel requires Node.js 18 or higher"
    exit 1
fi
echo "✅ Node.js version: $(node -v)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found, installing...${NC}"
    npm install
fi
echo "✅ Dependencies installed"

# Run build test
echo ""
echo "🔨 Testing production build..."
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Build successful!${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Run 'npm run build' to see errors"
    exit 1
fi

# Check for environment variables
echo ""
echo "🔑 Checking environment variables..."
if [ -f ".env.local" ]; then
    echo "✅ Found .env.local"
    if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
        echo "✅ NEXT_PUBLIC_API_URL is set locally"
    else
        echo -e "${YELLOW}⚠️  NEXT_PUBLIC_API_URL not found in .env.local${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No .env.local file found${NC}"
    echo "   This is OK, but remember to set NEXT_PUBLIC_API_URL in Vercel"
fi

# Check for .vercelignore
echo ""
echo "📁 Checking deployment configuration..."
if [ -f "../vercel.json" ]; then
    echo "✅ Found vercel.json"
else
    echo -e "${YELLOW}⚠️  No vercel.json found${NC}"
fi

if [ -f "../.vercelignore" ]; then
    echo "✅ Found .vercelignore"
else
    echo -e "${YELLOW}⚠️  No .vercelignore found${NC}"
fi

# Check git status
echo ""
echo "📦 Checking git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    if git diff-index --quiet HEAD --; then
        echo "✅ No uncommitted changes"
    else
        echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
        echo "   Commit your changes before deploying"
    fi
    
    # Check if remote exists
    if git remote | grep -q "origin"; then
        echo "✅ Git remote 'origin' configured"
    else
        echo -e "${YELLOW}⚠️  No git remote configured${NC}"
        echo "   Add a remote: git remote add origin <url>"
    fi
else
    echo -e "${RED}❌ Not a git repository${NC}"
    echo "   Initialize git: git init"
    exit 1
fi

# Check package.json scripts
echo ""
echo "📜 Verifying package.json scripts..."
if grep -q '"build"' package.json; then
    echo "✅ Build script found"
else
    echo -e "${RED}❌ No build script in package.json${NC}"
    exit 1
fi

if grep -q '"start"' package.json; then
    echo "✅ Start script found"
else
    echo -e "${RED}❌ No start script in package.json${NC}"
    exit 1
fi

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}🎉 Pre-deployment checks complete!${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Commit and push your code to Git"
echo "   2. Go to https://vercel.com/new"
echo "   3. Import your repository"
echo "   4. Set NEXT_PUBLIC_API_URL in Vercel dashboard"
echo "   5. Deploy!"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - web/DEPLOYMENT.md"
echo "   - VERCEL_DEPLOYMENT.md"
echo "   - DEPLOYMENT_CHECKLIST.md"
echo ""
