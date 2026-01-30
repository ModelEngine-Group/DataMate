import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path"; // 需要安装 Node.js 的类型声明（@types/node）

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"), // 将 @/ 映射到 src/ 目录
    },
  },
  server: {
    host: "0.0.0.0",
    proxy: (() => {
      const pythonProxyConfig = {
        target: "http://localhost:18000",
        changeOrigin: true,
        secure: false,
        configure: (proxy: { on: (event: string, handler: (arg: unknown) => void) => void }) => {
          proxy.on("proxyReq", (proxyReq: unknown) => {
            (proxyReq as { removeHeader: (name: string) => void }).removeHeader("referer");
            (proxyReq as { removeHeader: (name: string) => void }).removeHeader("origin");
          });
          proxy.on("proxyRes", (proxyRes: unknown) => {
            const res = proxyRes as { headers: Record<string, unknown> };
            delete res.headers["set-cookie"];
            res.headers["cookies"] = "";
          });
        },
      };

      const javaProxyConfig = {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
        configure: (proxy: { on: (event: string, handler: (arg: unknown) => void) => void }) => {
          proxy.on("proxyReq", (proxyReq: unknown) => {
            (proxyReq as { removeHeader: (name: string) => void }).removeHeader("referer");
            (proxyReq as { removeHeader: (name: string) => void }).removeHeader("origin");
          });
          proxy.on("proxyRes", (proxyRes: unknown) => {
            const res = proxyRes as { headers: Record<string, unknown> };
            delete res.headers["set-cookie"];
            res.headers["cookies"] = "";
          });
        },
      };

      // Python 服务: rag, synthesis, annotation, evaluation, models
      const pythonPaths = ["rag", "synthesis", "annotation", "data-collection", "evaluation", "models"];
      // Java 服务: data-management, knowledge-base
      const javaPaths = ["data-management", "knowledge-base", "operators"];

      const proxy: Record<string, object> = {};
      for (const p of pythonPaths) {
        proxy[`/api/${p}`] = pythonProxyConfig;
      }
      for (const p of javaPaths) {
        proxy[`/api/${p}`] = javaProxyConfig;
      }
      return proxy;
    })(),
  },
});
