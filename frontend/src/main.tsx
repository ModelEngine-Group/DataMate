import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp, Spin } from "antd";
import "./index.css";
import TopLoadingBar from "./components/TopLoadingBar";
import { store } from "./store";
import { Provider } from "react-redux";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Provider store={store}>
      <AntdApp>
        <Suspense fallback={<Spin />}>
          <TopLoadingBar />
          <RouterProvider router={router} />
        </Suspense>
      </AntdApp>
    </Provider>
  </StrictMode>
);
