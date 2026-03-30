import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp, Spin, ConfigProvider } from "antd";
import "./index.css";
import TopLoadingBar from "./components/TopLoadingBar";
import AuthGuard from "./components/AuthGuard";
import { store } from "./store";
import { Provider } from "react-redux";
import theme from "./theme";
import {errorConfigStore} from "@/utils/errorConfigStore.ts";
import "@/i18n";

function showLoadingUI() {
  const container = document.getElementById("root");
  if (!container) return;
  
  container.innerHTML = `
    <div style="
      min-height: 100vh;
      background: linear-gradient(to bottom right, #eff6ff, #e0e7ff);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="text-align: center;">
        <div style="
          width: 40px;
          height: 40px;
          border: 3px solid #e5e7eb;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        "></div>
        <style>
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        </style>
      </div>
    </div>
  `;
}

/**
 * 自定义首页URL重定向
 * 在任何渲染之前检查系统参数 sys.home.page.url，若已配置则立即跳转，确保无闪烁。
 * 使用原始 fetch 避免触发 antd message 等尚未初始化的 UI 组件。
 */
async function checkHomePageRedirect(): Promise<boolean> {
  if (window.location.pathname !== '/') {
    return false;
  }
  try {
    const response = await fetch('/api/sys-param/sys.home.page.url', {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (response.ok) {
      const result = await response.json();
      const url = result?.data?.paramValue?.trim();
      if (url) {
        window.location.replace(url);
        return true;
      }
    }
  } catch {
    // 忽略错误，继续正常启动
  }
  return false;
}

async function bootstrap() {
  const container = document.getElementById("root");
  if (!container) return;

  // 在任何 UI 渲染之前检查自定义首页重定向
  if (await checkHomePageRedirect()) {
    return;
  }

  showLoadingUI();

  try {
    await errorConfigStore.loadConfig();
  } catch (e) {
    console.error('Config load failed:', e);
  }

  const root = createRoot(container);
  
  root.render(
    <StrictMode>
      <Provider store={store}>
        <ConfigProvider theme={ theme }>
          <AntdApp>
            <Suspense fallback={<Spin />}>
              <TopLoadingBar />
              <AuthGuard />
              <RouterProvider router={router} />
            </Suspense>
          </AntdApp>
        </ConfigProvider>
      </Provider>
    </StrictMode>
  );
}

bootstrap();
