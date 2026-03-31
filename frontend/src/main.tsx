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
import { setCachedHomePageUrl, getCachedHomePageUrl } from "@/utils/systemParam";
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
 * 从 localStorage 读取 JWT token
 */
function getAuthToken(): string | null {
  const session = localStorage.getItem('session');
  if (session) {
    try {
      return JSON.parse(session).token || null;
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * 自定义首页URL重定向
 * 在任何渲染之前检查系统参数 sys.home.page.url，若已配置则立即跳转，确保无闪烁。
 * 使用原始 fetch 但携带 JWT token，避免已登录用户仍收到 401。
 */
async function checkHomePageRedirect(): Promise<{ redirected: boolean; authNeeded: boolean }> {
  if (window.location.pathname !== '/') {
    return { redirected: false, authNeeded: false };
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch('/api/sys-param/sys.home.page.url', {
      method: 'GET',
      credentials: 'include',
      headers,
    });
    if (response.ok) {
      const result = await response.json();
      const url = result?.data?.paramValue?.trim();
      if (url) {
        setCachedHomePageUrl(url);
        window.location.replace(url);
        return { redirected: true, authNeeded: false };
      }
      // 参数存在但值为空 → 管理员已清除，清掉缓存
      setCachedHomePageUrl(null);
    } else if (response.status === 401) {
      // 未登录，尝试从缓存读取
      const cachedUrl = getCachedHomePageUrl();
      if (cachedUrl) {
        window.location.replace(cachedUrl);
        return { redirected: true, authNeeded: false };
      }
      // 未登录且无缓存，需要弹出登录框
      return { redirected: false, authNeeded: true };
    }
  } catch {
    // 网络错误等，尝试从缓存读取
    const cachedUrl = getCachedHomePageUrl();
    if (cachedUrl) {
      window.location.replace(cachedUrl);
      return { redirected: true, authNeeded: false };
    }
  }
  return { redirected: false, authNeeded: false };
}

async function bootstrap() {
  const container = document.getElementById("root");
  if (!container) return;

  // 在任何 UI 渲染之前检查自定义首页重定向
  const { redirected, authNeeded } = await checkHomePageRedirect();
  if (redirected) {
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

  // 未登录且无缓存时，等 React 挂载后弹出登录框
  if (authNeeded) {
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('show-login'));
    }, 500);
  }
}

bootstrap();
