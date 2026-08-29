/** @type {import('next').NextConfig} */
const nextConfig = {
  // NEXT_API_BASE has no NEXT_PUBLIC_ prefix, so Next.js wouldn't normally
  // inline it into client-side code. This `env` key is the documented
  // escape hatch: it explicitly exposes the named var to both server and
  // browser bundles at build time, regardless of prefix.
  env: {
    NEXT_API_BASE: process.env.NEXT_API_BASE,
  },
};

export default nextConfig;
