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
    headers: {
      "Access-Control-Allow-Origin": "*",
      'access-control-allow-headers': "Origin, X-Requested-With, Content-Type, Accept",
    },
    proxy: {
      "/api": 'http://localhost:8002'
    }
  }
});
