import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp, Spin } from "antd";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Suspense fallback={<Spin />}>
      <AntdApp>
        <RouterProvider router={router} />
      </AntdApp>
    </Suspense>
  </StrictMode>
);
