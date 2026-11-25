import type { NextConfig } from "next";

const API_ORIGIN = process.env.LABPULSE_API_ORIGIN ?? "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  /* Same-origin proxy so the PDF iframe is not cross-origin (avoids black preview). */
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  cacheComponents: true,
  partialPrefetching: true,
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${API_ORIGIN}/:path*`,
      },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
