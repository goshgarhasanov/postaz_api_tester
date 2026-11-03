import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: the React app runs on 5173 and proxies /api to the Express backend
// so the browser never hits a cross-origin wall during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:5177",
        changeOrigin: true,
      },
    },
  },
});



