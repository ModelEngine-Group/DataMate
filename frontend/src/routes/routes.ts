import { createBrowserRouter } from "react-router";
import Home from "../pages/Home/Home";
import MainLayout from "../pages/Layout/MainLayout";

import DatasetManagement from "@/pages/DataManagement/Home/DataManagement";
import DatasetCreate from "@/pages/DataManagement/Create/CreateDataset";
import DatasetDetail from "@/pages/DataManagement/Detail/DatasetDetail";

import DataCleansing from "@/pages/DataCleansing/Home/DataCleansing";
import CleansingTaskCreate from "@/pages/DataCleansing/Create/CreateTask";
import CleansingTaskDetail from "@/pages/DataCleansing/Detail/TaskDetail";
import CleansingTemplateCreate from "@/pages/DataCleansing/Create/CreateTemplate";

import OperatorMarketPage from "@/pages/OperatorMarket/Home/OperatorMarket";
import OperatorPluginCreate from "@/pages/OperatorMarket/Create/OperatorPluginCreate";
import OperatorPluginDetail from "@/pages/OperatorMarket/Detail/OperatorPluginDetail";
import SmartOrchestrationPage from "@/pages/Orchestration/SmartOrchestration";
import WorkflowEditor from "@/pages/Orchestration/WorkflowEditor";
import { withErrorBoundary } from "@/components/ErrorBoundary";
import AgentPage from "@/pages/Agent/Agent.tsx";
import CleansingTemplateDetail from "@/pages/DataCleansing/Detail/TemplateDetail";

const router = createBrowserRouter([
  {
    path: "/",
    Component: withErrorBoundary(Home),
  },
  {
    path: "/chat",
    Component: withErrorBoundary(AgentPage),
  },
  {
    path: "/orchestration",
    children: [
      {
        path: "",
        index: true,
        Component: withErrorBoundary(SmartOrchestrationPage),
      },
      {
        path: "create-workflow",
        Component: withErrorBoundary(WorkflowEditor),
      },
    ],
  },
  {
    path: "/data",
    Component: withErrorBoundary(MainLayout),
    children: [
      {
        path: "management",
        children: [
          {
            path: "",
            index: true,
            Component: DatasetManagement,
          },
          {
            path: "create/:id?",
            Component: DatasetCreate,
          },
          {
            path: "detail/:id",
            Component: DatasetDetail,
          },
        ],
      },
      {
        path: "cleansing",
        children: [
          {
            path: "",
            index: true,
            Component: DataCleansing,
          },
          {
            path: "create-task",
            Component: CleansingTaskCreate,
          },
          {
            path: "task-detail/:id",
            Component: CleansingTaskDetail,
          },
          {
            path: "create-template",
            Component: CleansingTemplateCreate,
          },
          {
            path: "template-detail/:id",
            Component: CleansingTemplateDetail,
          },
          {
            path: "update-template/:id",
            Component: CleansingTemplateCreate,
          },
        ],
      },
      {
        path: "operator-market",
        children: [
          {
            path: "",
            index: true,
            Component: OperatorMarketPage,
          },
          {
            path: "create/:id?",
            Component: OperatorPluginCreate,
          },
          {
            path: "plugin-detail/:id",
            Component: OperatorPluginDetail,
          },
        ],
      },
    ],
  },
]);

export default router;
