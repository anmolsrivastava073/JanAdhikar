import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["framer-motion", "recharts", "lucide-react"],
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    if (process.env.NODE_ENV === "development" || process.env.BACKEND_URL) {
      const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";
      return [
        {
          source: "/api/:path*",
          destination: `${backendUrl}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
