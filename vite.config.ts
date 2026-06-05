import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: false,
  },
  resolve: {
    alias: {
      "node:async_hooks": fileURLToPath(new URL("./src/polyfills/async_hooks.ts", import.meta.url)),
    },
  },
});
