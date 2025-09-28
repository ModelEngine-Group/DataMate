import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp, Spin } from "antd";
import "./index.css";
import TopLoadingBar from "./components/TopLoadingBar";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AntdApp>
      <Suspense fallback={<Spin />}>
        <TopLoadingBar />
        <RouterProvider router={router} />
      </Suspense>
    </AntdApp>
  </StrictMode>
);
