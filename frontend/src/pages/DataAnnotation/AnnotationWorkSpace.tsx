import { useEffect, useState } from "react";
import { Card, message } from "antd";
import { Button, Badge, Progress, Checkbox } from "antd";
import {
  ArrowLeft,
  FileText,
  ImageIcon,
  Video,
  Music,
  Save,
  SkipForward,
  CheckCircle,
  Eye,
  Settings,
} from "lucide-react";
import { mockTasks } from "@/mock/annotation";
import { Outlet, useNavigate } from "react-router";

export default function AnnotationWorkspace() {
  const navigate = useNavigate();
  const [task, setTask] = useState(mockTasks[0]);

  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [annotationProgress, setAnnotationProgress] = useState({
    completed: task.completedCount,
    skipped: task.skippedCount,
    total: task.totalCount,
  });

  const handleSaveAndNext = () => {
    setAnnotationProgress((prev) => ({
      ...prev,
      completed: prev.completed + 1,
    }));

    if (currentFileIndex < task.totalCount - 1) {
      setCurrentFileIndex(currentFileIndex + 1);
    }

    message({
      title: "标注已保存",
      description: "标注结果已保存，自动跳转到下一个",
    });
  };

  const handleSkipAndNext = () => {
    setAnnotationProgress((prev) => ({
      ...prev,
      skipped: prev.skipped + 1,
    }));

    if (currentFileIndex < task.totalCount - 1) {
      setCurrentFileIndex(currentFileIndex + 1);
    }

    message({
      title: "已跳过",
      description: "已跳过当前项目，自动跳转到下一个",
    });
  };

  const getDatasetTypeIcon = (type: string) => {
    switch (type) {
      case "text":
        return <FileText className="w-4 h-4 text-blue-500" />;
      case "image":
        return <ImageIcon className="w-4 h-4 text-green-500" />;
      case "video":
        return <Video className="w-4 h-4 text-purple-500" />;
      case "audio":
        return <Music className="w-4 h-4 text-orange-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const currentProgress = Math.round(
    ((annotationProgress.completed + annotationProgress.skipped) /
      annotationProgress.total) *
      100
  );

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Button
            type="text"
            onClick={() => navigate("/data/annotation")}
            icon={<ArrowLeft className="w-4 h-4" />}
          ></Button>
          <div className="flex items-center space-x-2">
            {getDatasetTypeIcon(task.datasetType)}
            <span className="text-xl font-bold">{task.name}</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600">
            {currentFileIndex + 1} / {task.totalCount}
          </div>
          <div className="flex items-center space-x-2 min-w-56">
            <span className="text-sm text-gray-600">进度:</span>
            <Progress
              percent={currentProgress}
              showInfo={false}
              className="w-24 h-2"
            />
            <span className="text-sm font-medium">{currentProgress}%</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex-1 flex">
        {/* Annotation Area */}
        <div className="flex-1 flex flex-col">
          <Outlet />
        </div>

        {/* Right Sidebar - Only show for text and image types */}
        {(task.datasetType === "text" || task.datasetType === "image") && (
          <div className="w-80 border-l border-gray-200 p-4 space-y-4">
            {/* Progress Stats */}
            <Card>
              <div className="space-y-3 pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">已完成</span>
                  <span className="font-medium text-green-500">
                    {annotationProgress.completed}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">已跳过</span>
                  <span className="font-medium text-red-500">
                    {annotationProgress.skipped}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">剩余</span>
                  <span className="font-medium text-gray-600">
                    {annotationProgress.total -
                      annotationProgress.completed -
                      annotationProgress.skipped}
                  </span>
                </div>
                <div className="border-t border-gray-200 my-3" />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">总进度</span>
                  <span className="font-medium">{currentProgress}%</span>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card>
              <div className="pt-4 space-y-2">
                <Button
                  type="primary"
                  block
                  onClick={handleSaveAndNext}
                  className="bg-green-500 border-green-500 hover:bg-green-600 hover:border-green-600"
                  icon={<CheckCircle className="w-4 h-4 mr-2" />}
                >
                  保存并下一个
                </Button>
                <Button
                  block
                  onClick={handleSkipAndNext}
                  icon={<SkipForward className="w-4 h-4 mr-2" />}
                >
                  跳过并下一个
                </Button>
                <Button block icon={<Save className="w-4 h-4 mr-2" />}>
                  仅保存
                </Button>
                <Button block icon={<Eye className="w-4 h-4 mr-2" />}>
                  预览结果
                </Button>
              </div>
            </Card>

            {/* Navigation */}
            <Card>
              <div className="pt-4 space-y-2">
                <div className="flex items-center space-x-2">
                  <Button
                    block
                    disabled={currentFileIndex === 0}
                    onClick={() => setCurrentFileIndex(currentFileIndex - 1)}
                  >
                    上一个
                  </Button>
                  <Button
                    block
                    disabled={currentFileIndex === task.totalCount - 1}
                    onClick={() => setCurrentFileIndex(currentFileIndex + 1)}
                  >
                    下一个
                  </Button>
                </div>
                <div className="text-xs text-gray-500">
                  当前: {currentFileIndex + 1} / {task.totalCount}
                </div>
              </div>
            </Card>

            {/* Settings */}
            <Card>
              <div className="pt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">自动保存</span>
                  <Checkbox defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">快捷键提示</span>
                  <Checkbox defaultChecked />
                </div>
                <Button block icon={<Settings className="w-4 h-4 mr-2" />}>
                  更多设置
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
