import { createBrowserRouter } from "react-router";
import Home from "../pages/Home/Home";
import MainLayout from "../pages/MainLayout";
import DatasetManagement from "@/pages/DataManagement/DataManagement";
import DatasetCreate from "@/pages/DataManagement/DatasetCreate";
import DatasetDetail from "@/pages/DataManagement/DatasetDetail";
import DataCollection from "@/pages/DataCollection/DataCollection";
import DataCleansing from "@/pages/DataCleansing/DataCleansing";
import CleansingTaskCreate from "@/pages/DataCleansing/CleansingTaskCreate";
import CleansingTaskDetail from "@/pages/DataCleansing/CleansingTaskDetail";
import CleansingTemplateCreate from "@/pages/DataCleansing/CleansingTemplateCreate";
import CollectionTaskCreate from "@/pages/DataCollection/CollectionTaskCreate";
import DataAnnotation from "@/pages/DataAnnotation/DataAnnotation";
import AnnotationTaskCreate from "@/pages/DataAnnotation/AnnotationTaskCreate";
import AnnotationWorkspace from "@/pages/DataAnnotation/AnnotationWorkSpace";
import TextAnnotationWorkspace from "@/pages/DataAnnotation/components/TextAnnotation";
import ImageAnnotationWorkspace from "@/pages/DataAnnotation/components/ImageAnnotation";
import AudioAnnotationWorkspace from "@/pages/DataAnnotation/components/AudioAnnotation";
import VideoAnnotationWorkspace from "@/pages/DataAnnotation/components/VideoAnnotation";
import DataEvaluationPage from "@/pages/DataEvaluation/DataEvaluation";
import EvaluationTaskCreate from "@/pages/DataEvaluation/EvaluationTaskCreate";
import EvaluationTaskReport from "@/pages/DataEvaluation/EvaluationTaskReport";
import ManualEvaluatePage from "@/pages/DataEvaluation/ManualEvaluate";
import KnowledgeGenerationPage from "@/pages/KnowledgeGeneration/KnowledgeGeneration";
import OperatorMarketPage from "@/pages/OperatorMarket/OperatorMarket";

const router = createBrowserRouter([
  {
    path: "/",
    Component: Home,
  },
  {
    path: "/data-orchestration",
    Component: () => "data-orchestration",
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
            path: "task-create",
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
            path: "task-create",
            Component: CleansingTaskCreate,
          },
          {
            path: "task-detail/:id",
            Component: CleansingTaskDetail,
          },
          {
            path: "template-create",
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
            path: "task-create",
            Component: AnnotationTaskCreate,
          },
          {
            path: "task-annotate",
            Component: AnnotationWorkspace,
            children: [
              {
                path: "text",
                Component: TextAnnotationWorkspace,
              },
              {
                path: "image",
                Component: ImageAnnotationWorkspace,
              },
              {
                path: "audio",
                Component: AudioAnnotationWorkspace,
              },
              {
                path: "video",
                Component: VideoAnnotationWorkspace,
              },
            ],
          },
        ],
      },
      {
        path: "synthesis-task",
        Component: () => "dataset",
      },
      {
        path: "ratio-task",
        Component: () => "dataset",
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
            path: "task-create",
            Component: EvaluationTaskCreate,
          },
          {
            path: "task-report/:id",
            Component: EvaluationTaskReport,
          },
          {
            path: "manual-evaluete/:id",
            Component: ManualEvaluatePage,
          },
        ],
      },
      {
        path: "knowledge-generation",
        Component: KnowledgeGenerationPage,
      },
      {
        path: "operator-market",
        Component: OperatorMarketPage,
      },
    ],
  },
]);

export default router;
