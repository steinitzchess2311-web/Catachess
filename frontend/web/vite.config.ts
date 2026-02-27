import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  define: {
    'process.env': {},
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@ui": path.resolve(__dirname, "../ui"),
      "@patch": path.resolve(__dirname, "../../patch"),
      // Resolve chess.js for patch directory files
      "chess.js": path.resolve(__dirname, "node_modules/chess.js"),
      "@radix-ui/react-icons": path.resolve(__dirname, "node_modules/@radix-ui/react-icons"),
    },
    // Ensure modules are resolved from frontend/web/node_modules for patch files
    dedupe: ["react", "react-dom", "react-router-dom", "chess.js", "react-chessboard"],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react-router-dom", "chess.js", "react-chessboard", "@radix-ui/react-icons"],
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, ".."), path.resolve(__dirname, "../../patch")],
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    commonjsOptions: {
      include: [/node_modules/],
    },
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('/node_modules/react/') || id.includes('/node_modules/react-dom/') || id.includes('/node_modules/react-router')) {
            return 'vendor-react';
          }
          if (id.includes('/node_modules/chess.js') || id.includes('/node_modules/react-chessboard')) {
            return 'vendor-chess';
          }
        },
      },
    },
  },
});
