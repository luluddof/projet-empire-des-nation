import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

/**
 * Les appels API passent par le même origine (ex. http://localhost:5173/api/...)
 * pour que le cookie de session Flask soit bien envoyé (pas de mélange 5173 / 5000).
 * En Docker : définir VITE_PROXY_TARGET=http://backend:5000
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget =
    env.VITE_PROXY_TARGET ||
    process.env.VITE_PROXY_TARGET ||
    "http://127.0.0.1:5000";

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        "/api": {
          target: proxyTarget,
          // false = garde le Host du navigateur (localhost:5173). Sinon Flask voit
          // "backend:5000" et le Set-Cookie ne correspond pas à l’origine de la page.
          changeOrigin: false,
        },
      },
    },
  };
});
