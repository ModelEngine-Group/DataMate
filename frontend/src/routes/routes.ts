import { createBrowserRouter } from "react-router";
import Home from "../pages/Home/Home";
import MainLayout from "../pages/Layout/MainLayout";

import DataCollection from "@/pages/DataCollection/Home/DataCollectionPage";
import CollectionTaskCreate from "@/pages/DataCollection/Create/CreateTask";

import DatasetManagement from "@/pages/DataManagement/Home/DataManagement";
import DatasetCreate from "@/pages/DataManagement/Create/CreateDataset";
import DatasetDetail from "@/pages/DataManagement/Detail/DatasetDetail";

import DataCleansing from "@/pages/DataCleansing/Home/DataCleansing";
import CleansingTaskCreate from "@/pages/DataCleansing/Create/CreateTask";
import CleansingTaskDetail from "@/pages/DataCleansing/Detail/TaskDetail";
import CleansingTemplateCreate from "@/pages/DataCleansing/Create/CreateTempate";

import DataAnnotation from "@/pages/DataAnnotation/Home/DataAnnotation";
import AnnotationTaskCreate from "@/pages/DataAnnotation/Create/CreateTask";

import DataSynthesisPage from "@/pages/SynthesisTask/DataSynthesis";
import InstructionTemplateCreate from "@/pages/SynthesisTask/CreateTemplate";
import SynthesisTaskCreate from "@/pages/SynthesisTask/CreateTask";

import DataEvaluationPage from "@/pages/DataEvaluation/Home/DataEvaluation";
import EvaluationTaskCreate from "@/pages/DataEvaluation/Create/CreateTask";
import EvaluationTaskReport from "@/pages/DataEvaluation/Report/EvaluationReport";
import ManualEvaluatePage from "@/pages/DataEvaluation/Evaluate/ManualEvaluate";

import KnowledgeBasePage from "@/pages/KnowledgeBase/Home/KnowledgeBasePage";
import KnowledgeBaseDetailPage from "@/pages/KnowledgeBase/Detail/KnowledgeBaseDetail";
import KnowledgeBaseFileDetailPage from "@/pages/KnowledgeBase/FileDetail/KnowledgeBaseFileDetail";

import OperatorMarketPage from "@/pages/OperatorMarket/Home/OperatorMarket";
import OperatorPluginCreate from "@/pages/OperatorMarket/Create/OperatorPluginCreate";
import OperatorPluginDetail from "@/pages/OperatorMarket/Detail/OperatorPluginDetail";
import RatioTasksPage from "@/pages/RatioTask/Home/RatioTask.tsx";
import CreateRatioTask from "@/pages/RatioTask/Create/CreateRatioTask.tsx";
import OrchestrationPage from "@/pages/Orchestration/Orchestration";
import WorkflowEditor from "@/pages/Orchestration/WorkflowEditor";
import { withErrorBoundary } from "@/components/ErrorBoundary";
import AgentPage from "@/pages/Agent/Agent.tsx";
import RatioTaskDetail from "@/pages/RatioTask/Detail/RatioTaskDetail";

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
        Component: withErrorBoundary(OrchestrationPage),
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
        path: "collection",
        children: [
          {
            path: "",
            index: true,
            Component: DataCollection,
          },
          {
            path: "create-task",
            Component: CollectionTaskCreate,
          },
        ],
      },
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
        ],
      },
      {
        path: "annotation",
        children: [
          {
            path: "",
            index: true,
            Component: DataAnnotation,
          },
          {
            path: "create-task",
            Component: AnnotationTaskCreate,
          },
        ],
      },
      {
        path: "synthesis/task",
        children: [
          {
            path: "",
            Component: DataSynthesisPage,
          },
          {
            path: "create-template",
            Component: InstructionTemplateCreate,
          },
          {
            path: "create",
            Component: SynthesisTaskCreate,
          },
        ],
      },
      {
        path: "synthesis/ratio-task",
        children: [
          {
            path: "",
            index: true,
            Component: RatioTasksPage,
          },
          {
            path: "create",
            Component: CreateRatioTask,
          },
          {
            path: "detail/:id",
            Component: RatioTaskDetail,
          }
        ],
      },
      {
        path: "evaluation",
        children: [
          {
            path: "",
            index: true,
            Component: DataEvaluationPage,
          },
          {
            path: "create-task",
            Component: EvaluationTaskCreate,
          },
          {
            path: "task-report/:id",
            Component: EvaluationTaskReport,
          },
          {
            path: "manual-evaluate/:id",
            Component: ManualEvaluatePage,
          },
        ],
      },
      {
        path: "knowledge-base",
        children: [
          {
            path: "",
            index: true,
            Component: KnowledgeBasePage,
          },
          {
            path: "detail/:id",
            Component: KnowledgeBaseDetailPage,
          },
          {
            path: "file-detail/:id",
            Component: KnowledgeBaseFileDetailPage,
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
