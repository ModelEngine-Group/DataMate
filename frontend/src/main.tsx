import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "./routes/routes";
import { App as AntdApp } from "antd";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AntdApp>
      <RouterProvider router={router} />
    </AntdApp>
  </StrictMode>
);
