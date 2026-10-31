import react from "@vitejs/plugin-react";
import basicSsl from "@vitejs/plugin-basic-ssl";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// `npm run dev`    -> http://localhost:5173, talks to the API at VITE_API_BASE_URL
// `npm run phone`  -> builds the app and serves it at https://<your-pc-ip>:5173 (self-signed) so a phone on the same
//                     Wi-Fi can open it and use the camera scanner (browsers only allow the camera on HTTPS).
//                     API calls go through this server at /api -> http://127.0.0.1:8000.
//
// Phone mode serves the finished build, not the dev server: the dev server keeps a live-reload WebSocket open, and on
// phones that reject the self-signed certificate for WebSockets it reloads the page over and over, which browsers
// report as "too many redirects".
const apiProxy = { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") } };

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss(), ...(mode === "phone" && !process.env.NO_TLS ? [basicSsl()] : [])],
  server: {
    port: 5173,
    ...(mode === "phone" ? { host: true, hmr: false, proxy: apiProxy } : {}),
  },
  // NO_TLS=1 serves the same build over plain http (set by start-phone.bat on port 5175) as a fallback if a phone will not take the self-signed certificate
preview: { host: true, port: Number(process.env.PREVIEW_PORT || 5173), strictPort: true, proxy: apiProxy },
}));
