import type { NextConfig } from "next";

const isDesktopBuild = process.env.NEXT_PUBLIC_BUILD_TARGET === "desktop";

const nextConfig: NextConfig = {
  images: { unoptimized: isDesktopBuild },
  ...(isDesktopBuild && {
    output: "export",
    trailingSlash: true,
  }),
};

export default nextConfig;
