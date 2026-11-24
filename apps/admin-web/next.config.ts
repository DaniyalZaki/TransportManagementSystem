import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Lets CI or a repair build avoid a stale local OneDrive `.next` reparse point.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};

export default nextConfig;
