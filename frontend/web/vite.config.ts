import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@ui": path.resolve(__dirname, "../ui"),
      "@patch": path.resolve(__dirname, "../../patch"),
      // Resolve chess.js for patch directory files
      "chess.js": path.resolve(__dirname, "node_modules/chess.js"),
    },
    // Ensure modules are resolved from frontend/web/node_modules for patch files
    dedupe: ["react", "react-dom", "react-router-dom", "chess.js"],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react-router-dom", "chess.js"],
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, ".."), path.resolve(__dirname, "../../patch")],
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    commonjsOptions: {
      include: [/node_modules/],
    },
  },
});
