import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In development the API runs separately (`ewf serve` on port 8000) and /api is proxied to it.
// `vite build --mode snapshot` (scripts/build-snapshot.mjs) embeds one forecast from EWF_SNAPSHOT
// and inlines every asset, for a single-file page that runs without the server.
export default defineConfig(({ mode }) => {
  const snapshot = mode === "snapshot" ? readFileSync(process.env.EWF_SNAPSHOT ?? "", "utf8") : "null";
  return {
    plugins: [react(), tailwindcss()],
    define: { __SNAPSHOT__: snapshot },
    server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
    build: mode === "snapshot"
      ? { outDir: "dist-snapshot", assetsInlineLimit: 100_000_000, cssCodeSplit: false, chunkSizeWarningLimit: 2000, rollupOptions: { output: { inlineDynamicImports: true } } }
      : { outDir: "dist", chunkSizeWarningLimit: 900 },
  };
});
