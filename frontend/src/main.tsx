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
import { setRequireLoginMode } from "@/utils/request";
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
async function checkHomePageRedirect(requireLogin: boolean, authenticated: boolean): Promise<{ redirected: boolean; authNeeded: boolean }> {
  if (window.location.pathname !== '/') {
    return { redirected: false, authNeeded: false };
  }

  // 尚未登录且要求登录时，检查是否有缓存的登录页URL
  if (requireLogin && !authenticated) {
    const cachedUrl = getCachedHomePageUrl();
    if (cachedUrl) {
      window.location.replace(cachedUrl);
      return { redirected: true, authNeeded: false };
    }
    // 需要登录且没有缓存URL，显示登录框
    return { redirected: false, authNeeded: true };
  }

  // 已认证或允许匿名访问时，检查自定义首页
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

/**
 * 检查登录策略和当前认证状态（从后端获取）
 * 这个检查应该在应用启动时总是执行，无论当前路径是什么
 */
async function checkLoginState(): Promise<{ requireLogin: boolean; authenticated: boolean }> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const userResponse = await fetch('/api/user/me', {
      method: 'GET',
      credentials: 'include',
      headers,
    });

    if (userResponse.ok) {
      const userResult = await userResponse.json();
      const requireLogin = userResult?.data?.requireLogin ?? false;
      const authenticated = userResult?.data?.authenticated === true;
      // 登录策略与认证状态分别保存，已登录时仍需处理后续令牌过期。
      setRequireLoginMode(requireLogin);
      return { requireLogin, authenticated };
    } else if (userResponse.status === 401) {
      // /api/user/me 本身返回 401，说明需要登录
      setRequireLoginMode(true);
      return { requireLogin: true, authenticated: false };
    }
  } catch (e) {
    console.error('[bootstrap] Failed to check login requirement:', e);
  }

  // 默认不需要登录
  setRequireLoginMode(false);
  return { requireLogin: false, authenticated: false };
}

async function bootstrap() {
  const container = document.getElementById("root");
  if (!container) return;

  // 首先检查是否需要登录（无论当前路径是什么）
  const { requireLogin, authenticated } = await checkLoginState();

  // 然后检查自定义首页重定向（只在根路径时）
  const { redirected, authNeeded } = await checkHomePageRedirect(requireLogin, authenticated);

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
