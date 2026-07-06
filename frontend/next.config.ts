import type { NextConfig } from "next";

const isDesktopBuild = process.env.NEXT_PUBLIC_BUILD_TARGET === "desktop";

const nextConfig: NextConfig = {
  ...(isDesktopBuild && {
    output: "export",
    images: { unoptimized: true },
  }),
};

export default nextConfig;
