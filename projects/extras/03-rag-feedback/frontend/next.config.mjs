/** @type {import('next').NextConfig} */
const nextConfig = {
  // Backend base URL; defaults to the local FastAPI service.
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000",
  },
};

export default nextConfig;
