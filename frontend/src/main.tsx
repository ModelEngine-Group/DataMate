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

async function checkHomePageRedirect(): Promise<string | null> {
  try {
    const response = await fetch('/api/sys-param/sys.home.page.url', {
      cache: 'no-store'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data?.paramValue?.trim() || null;
    }
  } catch (error) {
    console.error('Failed to fetch home page URL:', error);
  }

  return null;
}

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

async function bootstrap() {
  const container = document.getElementById("root");
  if (!container) return;

  showLoadingUI();

  try {
    const [, homePageUrl] = await Promise.all([
      errorConfigStore.loadConfig(),
      checkHomePageRedirect()
    ]);

    if (homePageUrl) {
      const currentPath = window.location.pathname;
      const targetPath = new URL(homePageUrl, window.location.origin).pathname;
      
      if (currentPath === '/' && currentPath !== targetPath) {
        window.location.href = homePageUrl;
        return;
      }
    }

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
