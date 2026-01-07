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

createRoot(document.getElementById("root")!).render(
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
