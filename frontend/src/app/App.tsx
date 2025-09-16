import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import router from "../routes/routes";

function App() {
  return (
    <StrictMode>
      <RouterProvider router={router} key="router" />
    </StrictMode>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
