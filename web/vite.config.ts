import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In development the API runs separately (`ewf serve` on port 8000) and /api is proxied to it.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
  build: { outDir: "dist", chunkSizeWarningLimit: 900 },
});
