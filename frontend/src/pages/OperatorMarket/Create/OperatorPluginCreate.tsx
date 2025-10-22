import { Button, Steps } from "antd";
import {
  ArrowLeft,
  CheckCircle,
  Settings,
  TagIcon,
  Upload,
} from "lucide-react";
import { useNavigate } from "react-router";
import { useCallback, useState } from "react";
import UploadStep from "./components/UploadStep";
import ParsingStep from "./components/ParsingStep";
import ConfigureStep from "./components/ConfigureStep";
import PreviewStep from "./components/PreviewStep";

interface ParsedOperatorInfo {
  name: string;
  version: string;
  description: string;
  author: string;
  category: string;
  modality: string[];
  type: "preprocessing" | "training" | "inference" | "postprocessing";
  framework: string;
  language: string;
  size: string;
  dependencies: string[];
  inputFormat: string[];
  outputFormat: string[];
  performance: {
    accuracy?: number;
    speed: string;
    memory: string;
  };
  documentation?: string;
  examples?: string[];
}

export default function OperatorPluginCreate() {
  const navigate = useNavigate();
  const [uploadStep, setUploadStep] = useState<
    "upload" | "parsing" | "configure" | "preview"
  >("upload");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [parseProgress, setParseProgress] = useState(0);
  const [parsedInfo, setParsedInfo] = useState<ParsedOperatorInfo | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  // 模拟文件上传
  const handleFileUpload = useCallback((files: FileList) => {
    setIsUploading(true);
    setParseError(null);

    // 模拟文件上传过程
    setTimeout(() => {
      const fileArray = Array.from(files).map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type,
      }));
      setUploadedFiles(fileArray);
      setIsUploading(false);
      setUploadStep("parsing");
      startParsing();
    }, 1000);
  }, []);

  // 模拟解析过程
  const startParsing = useCallback(() => {
    setParseProgress(0);
    const interval = setInterval(() => {
      setParseProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          // 模拟解析完成
          setTimeout(() => {
            setParsedInfo({
              name: "图像预处理算子",
              version: "1.2.0",
              description:
                "支持图像缩放、裁剪、旋转、颜色空间转换等常用预处理操作，优化了内存使用和处理速度",
              author: "当前用户",
              category: "图像处理",
              modality: ["image"],
              type: "preprocessing",
              framework: "PyTorch",
              language: "Python",
              size: "2.3MB",
              dependencies: [
                "opencv-python>=4.5.0",
                "pillow>=8.0.0",
                "numpy>=1.20.0",
              ],
              inputFormat: ["jpg", "png", "bmp", "tiff"],
              outputFormat: ["jpg", "png", "tensor"],
              performance: {
                accuracy: 99.5,
                speed: "50ms/image",
                memory: "128MB",
              },
              documentation:
                "# 图像预处理算子\n\n这是一个高效的图像预处理算子...",
              examples: [
                "from operator import ImagePreprocessor\nprocessor = ImagePreprocessor()\nresult = processor.process(image)",
              ],
            });
            setUploadStep("configure");
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  }, []);

  const handlePublish = () => {
    // 模拟发布过程
    setUploadStep("preview");
    setTimeout(() => {
      alert("算子发布成功！");
      // 这里可以重置状态或跳转到其他页面
    }, 2000);
  };

  return (
    <div className="flex-overflow-auto bg-gray-50">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button type="text" onClick={() => navigate("/data/operator-market")}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="text-xl font-bold text-gray-900">上传算子</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            items={[
              {
                title: "上传文件",
                icon: <Upload />,
              },
              {
                title: "解析文件",
                icon: <Settings />,
              },
              {
                title: "配置标签",
                icon: <TagIcon />,
              },
              {
                title: "发布完成",
                icon: <CheckCircle />,
              },
            ]}
            current={
              uploadStep === "upload"
                ? 0
                : uploadStep === "parsing"
                ? 1
                : uploadStep === "configure"
                ? 2
                : 3
            }
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-overflow-auto p-6 mt-4 bg-white border-card">
        <div className="flex-overflow-auto">
          {uploadStep === "upload" && (
            <UploadStep onUpload={handleFileUpload} isUploading={isUploading} />
          )}
          {uploadStep === "parsing" && (
            <ParsingStep
              parseProgress={parseProgress}
              uploadedFiles={uploadedFiles}
            />
          )}
          {uploadStep === "configure" && (
            <ConfigureStep
              setUploadStep={setUploadStep}
              parseError={parseError}
              parsedInfo={parsedInfo}
            />
          )}
          {uploadStep === "preview" && (
            <PreviewStep setUploadStep={setUploadStep} />
          )}
        </div>
        {uploadStep === "configure" && (
          <div className="flex justify-end gap-3 mt-8">
            <Button onClick={() => setUploadStep("upload")}>重新上传</Button>
            <Button onClick={() => setUploadStep("preview")}>预览</Button>
            <Button type="primary" onClick={handlePublish}>
              发布算子
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
