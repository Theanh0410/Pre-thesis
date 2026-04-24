/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/chat",
        destination: "http://127.0.0.1:5000/api/chat", // proxy tới Flask
      },
    ];
  },
};

module.exports = nextConfig;
