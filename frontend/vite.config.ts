import { defineConfig } from "vite";
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
    // headers: {
    //   "Access-Control-Allow-Origin": "*",
    //   "access-control-allow-headers":
    //     "Origin, X-Requested-With, Content-Type, Accept",
    // },
    proxy: {
      "^/api": {
        // target: "http://localhost:8002", // 本地后端服务地址
        target: "http://1.94.5.242:32530", // 远程后端服务地址
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, "/api"),
        configure: (proxy, options) => {
          // proxy 是 'http-proxy' 的实例
          proxy.on("proxyReq", (proxyReq, req, res) => {
            // 可以在这里修改请求头
            proxyReq.removeHeader("referer");
            proxyReq.removeHeader("origin");
          });
          proxy.on("proxyRes", (proxyRes, req, res) => {
            delete proxyRes.headers["set-cookie"];
            proxyRes.headers["cookies"] = ""; // 清除 cookies 头
          });
        },
      },
    },
  },
});
