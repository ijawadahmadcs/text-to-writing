import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  // Allow access to remote image placeholder.
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**', // This allows any path under the hostname
      },
    ],
  },
  // 'standalone' output for self-hosted deployments; Vercel handles this automatically
  output: process.env.VERCEL ? undefined : 'standalone',
  transpilePackages: ['motion'],
  // Local dev only: proxy Python API routes to Flask dev server.
  // On Vercel, vercel.json rewrites handle routing to the Python function.
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [
      { source: '/api/generate', destination: 'http://127.0.0.1:5328/api/generate' },
      { source: '/api/fonts', destination: 'http://127.0.0.1:5328/api/fonts' },
      { source: '/api/templates', destination: 'http://127.0.0.1:5328/api/templates' },
      { source: '/api/analyze', destination: 'http://127.0.0.1:5328/api/analyze' },
      { source: '/api/analyze-template', destination: 'http://127.0.0.1:5328/api/analyze-template' },
    ];
  },
  webpack: (config, {dev}) => {
    // HMR is disabled in AI Studio via DISABLE_HMR env var.
    // Do not modifyâfile watching is disabled to prevent flickering during agent edits.
    if (dev && process.env.DISABLE_HMR === 'true') {
      config.watchOptions = {
        ignored: /.*/,
      };
    }
    return config;
  },
};

export default nextConfig;
