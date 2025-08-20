import { createBrowserRouter } from "react-router";
import Home from "../pages/Home/Home";
import MainLayout from "../pages/Layout/MainLayout";

import DataCollection from "@/pages/DataCollection/DataCollection";
import CollectionTaskCreate from "@/pages/DataCollection/CreateTask";

import DatasetManagement from "@/pages/DataManagement/DataManagement";
import DatasetCreate from "@/pages/DataManagement/CreateDataset";
import DatasetDetail from "@/pages/DataManagement/DatasetDetail";

import DataCleansing from "@/pages/DataCleansing/DataCleansing";
import CleansingTaskCreate from "@/pages/DataCleansing/CreateTask";
import CleansingTaskDetail from "@/pages/DataCleansing/TaskDetail";
import CleansingTemplateCreate from "@/pages/DataCleansing/CreateTempate";

import DataAnnotation from "@/pages/DataAnnotation/DataAnnotation";
import AnnotationTaskCreate from "@/pages/DataAnnotation/CreateTask";
import AnnotationWorkspace from "@/pages/DataAnnotation/AnnotationWorkSpace";
import TextAnnotationWorkspace from "@/pages/DataAnnotation/components/TextAnnotation";
import ImageAnnotationWorkspace from "@/pages/DataAnnotation/components/ImageAnnotation";
import AudioAnnotationWorkspace from "@/pages/DataAnnotation/components/AudioAnnotation";
import VideoAnnotationWorkspace from "@/pages/DataAnnotation/components/VideoAnnotation";

import DataSynthesisPage from "@/pages/SynthesisTask/DataSynthesis";
import InstructionTemplateCreate from "@/pages/SynthesisTask/CreateTemplate";
import SynthesisTaskCreate from "@/pages/SynthesisTask/CreateTask";

import DataEvaluationPage from "@/pages/DataEvaluation/DataEvaluation";
import EvaluationTaskCreate from "@/pages/DataEvaluation/CreateTask";
import EvaluationTaskReport from "@/pages/DataEvaluation/EvaluationReport";
import ManualEvaluatePage from "@/pages/DataEvaluation/ManualEvaluate";

import KnowledgeGenerationPage from "@/pages/KnowledgeGeneration/KnowledgeGeneration";
import KnowledgeBaseCreatePage from "@/pages/KnowledgeGeneration/KnowledgeBaseCreate";
import KnowledgeBaseDetailPage from "@/pages/KnowledgeGeneration/KnowledgeBaseDetail";
import KnowledgeBaseFileDetailPage from "@/pages/KnowledgeGeneration/KnowledgeBaseFileDetail";

import OperatorMarketPage from "@/pages/OperatorMarket/OperatorMarket";
import OperatorPluginCreate from "@/pages/OperatorMarket/UploadOperator";
import OperatorPluginDetail from "@/pages/OperatorMarket/OperatorPluginDetail";
import RatioTasksPage from "@/pages/RatioTask/RatioTask";
import CreateRatioTask from "@/pages/RatioTask/CreateRatioTask";
import OrchestrationPage from "@/pages/Orchestration/Orchestration";
import WorkflowEditor from "@/pages/Orchestration/WorkflowEditor";
import AgentPage from "@/pages/Agent/Agent";
import SettingsPage from "@/pages/SettingsPage/Settings";

const router = createBrowserRouter([
  {
    path: "/",
    Component: Home,
  },
  {
    path: "/agent",
    Component: AgentPage,
  },
  {
    path: "/orchestration",
    children: [
      {
        path: "",
        index: true,
        Component: OrchestrationPage,
      },
      {
        path: "create-workflow",
        Component: WorkflowEditor,
      },
    ],
  },
  {
    path: "/data",
    Component: MainLayout,
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
            path: "create",
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
          {
            path: "task-annotate",
            Component: AnnotationWorkspace,
            children: [
              {
                path: "text/:id",
                Component: TextAnnotationWorkspace,
              },
              {
                path: "image/:id",
                Component: ImageAnnotationWorkspace,
              },
              {
                path: "audio/:id",
                Component: AudioAnnotationWorkspace,
              },
              {
                path: "video/:id",
                Component: VideoAnnotationWorkspace,
              },
            ],
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
        path: "knowledge-generation",
        children: [
          {
            path: "",
            index: true,
            Component: KnowledgeGenerationPage,
          },
          {
            path: "create/:id?",
            Component: KnowledgeBaseCreatePage,
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
            path: "upload-operator",
            Component: OperatorPluginCreate,
          },
          {
            path: "plugin-detail/:id",
            Component: OperatorPluginDetail,
          },
        ],
      },
      {
        path: "settings",
        Component: SettingsPage,
      },
    ],
  },
]);

export default router;
