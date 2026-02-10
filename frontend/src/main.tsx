import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp, Spin, ConfigProvider } from "antd";
import "./index.css";
import TopLoadingBar from "./components/TopLoadingBar";
import { store } from "./store";
import { Provider } from "react-redux";
import theme from "./theme";
import {errorConfigStore} from "@/utils/errorConfigStore.ts";
import "@/i18n";

async function bootstrap() {
  const container = document.getElementById("root");
  if (!container) return;

  const root = createRoot(container);

  try {
    // 2. 【关键步骤】在渲染前，等待配置文件加载完成
    // 这一步会发起 fetch 请求去拿 /config/error-code.json
    await errorConfigStore.loadConfig();

  } catch (e) {
    // 容错处理：即使配置文件加载失败（比如404），也不应该导致整个 App 白屏崩溃
    // 此时 App 会使用代码里的默认兜底文案
    console.error('Error config load failed, using default messages.', e);
  } finally {
    // 3. 无论配置加载成功与否，最后都执行渲染
    root.render(
      <StrictMode>
        <Provider store={store}>
          <ConfigProvider theme={ theme }>
            <AntdApp>
              <Suspense fallback={<Spin />}>
                <TopLoadingBar />
                <RouterProvider router={router} />
              </Suspense>
            </AntdApp>
          </ConfigProvider>
        </Provider>
      </StrictMode>
    );
  }
}

// 4. 执行启动
bootstrap();
