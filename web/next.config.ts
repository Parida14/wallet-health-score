import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  
  // Enable standalone output for Docker deployment (disable for Vercel)
  output: process.env.VERCEL ? undefined : 'standalone',
  
  // Configure allowed image domains if needed
  images: {
    remotePatterns: [],
  },
  
  // Environment variables that should be available on the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
