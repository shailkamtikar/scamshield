import react from "@vitejs/plugin-react";
import basicSsl from "@vitejs/plugin-basic-ssl";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// `npm run dev`        -> http://localhost:5173, talks to the API at VITE_API_BASE_URL
// `npm run dev:phone`  -> https://<your-pc-ip>:5173 (self-signed) so a phone can use the
//                         camera scanner (browsers only allow camera access on HTTPS).
//                         API calls go through the dev server at /api -> http://127.0.0.1:8000
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss(), ...(mode === "phone" ? [basicSsl()] : [])],
  server: {
    port: 5173,
    ...(mode === "phone"
      ? {
          host: true,
          proxy: {
            "/api": { target: "http://127.0.0.1:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
          },
        }
      : {}),
  },
}));
