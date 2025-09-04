import { useState, useCallback } from "react";
import { Card, Button, Input, Progress, Alert, Spin, Steps } from "antd";
import {
  Upload,
  FileText,
  CheckCircle,
  Settings,
  TagIcon,
  Plus,
  X,
  Eye,
} from "lucide-react";

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

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  content?: string;
}

export default function OperatorUploadPage() {
  const [uploadStep, setUploadStep] = useState<
    "upload" | "parsing" | "configure" | "preview"
  >("upload");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [parseProgress, setParseProgress] = useState(0);
  const [parsedInfo, setParsedInfo] = useState<ParsedOperatorInfo | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customTag, setCustomTag] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const availableTags = [
    "图像处理",
    "预处理",
    "缩放",
    "裁剪",
    "旋转",
    "文本处理",
    "分词",
    "中文",
    "NLP",
    "医学",
    "音频处理",
    "特征提取",
    "MFCC",
    "频谱分析",
    "视频处理",
    "帧提取",
    "关键帧",
    "采样",
    "多模态",
    "融合",
    "深度学习",
    "注意力机制",
    "推理加速",
    "TensorRT",
    "优化",
    "GPU",
    "数据增强",
    "几何变换",
    "颜色变换",
    "噪声",
  ];

  const supportedFormats = [
    { ext: ".py", desc: "Python 脚本文件" },
    { ext: ".zip", desc: "压缩包文件" },
    { ext: ".tar.gz", desc: "压缩包文件" },
    { ext: ".whl", desc: "Python Wheel 包" },
    { ext: ".yaml", desc: "配置文件" },
    { ext: ".yml", desc: "配置文件" },
    { ext: ".json", desc: "JSON 配置文件" },
  ];

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

  const handleAddCustomTag = () => {
    if (customTag.trim() && !selectedTags.includes(customTag.trim())) {
      setSelectedTags([...selectedTags, customTag.trim()]);
      setCustomTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setSelectedTags(selectedTags.filter((tag) => tag !== tagToRemove));
  };

  const handlePublish = () => {
    // 模拟发布过程
    setUploadStep("preview");
    setTimeout(() => {
      alert("算子发布成功！");
      // 这里可以重置状态或跳转到其他页面
    }, 2000);
  };

  const renderUploadStep = () => (
    <div className="w-full mx-auto">
      <Card className="text-center">
        <div className="py-2">
          <div className="w-24 h-24 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center">
            <Upload className="w-12 h-12 text-blue-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            上传算子文件
          </h2>
          <p className="text-gray-600 mb-8">
            支持多种格式的算子文件，系统将自动解析配置信息
          </p>

          {/* 支持的格式 */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              支持的文件格式
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {supportedFormats.map((format, index) => (
                <div
                  key={index}
                  className="p-3 border border-gray-200 rounded-lg"
                >
                  <div className="font-medium text-gray-900">{format.ext}</div>
                  <div className="text-sm text-gray-500">{format.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 文件上传区域 */}
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-blue-400 transition-colors cursor-pointer"
            onDrop={(e) => {
              e.preventDefault();
              const files = e.dataTransfer.files;
              if (files.length > 0) {
                handleFileUpload(files);
              }
            }}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => {
              const input = document.createElement("input");
              input.type = "file";
              input.multiple = true;
              input.accept = supportedFormats.map((f) => f.ext).join(",");
              input.onchange = (e) => {
                const files = (e.target as HTMLInputElement).files;
                if (files) {
                  handleFileUpload(files);
                }
              };
              input.click();
            }}
          >
            {isUploading ? (
              <div className="flex flex-col items-center">
                <Spin size="large" />
                <p className="mt-4 text-gray-600">正在上传文件...</p>
              </div>
            ) : (
              <div>
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg text-gray-600 mb-2">
                  拖拽文件到此处或点击选择文件
                </p>
                <p className="text-sm text-gray-500">
                  支持单个文件或多个文件同时上传
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );

  const renderParsingStep = () => (
    <div className="w-full mx-auto">
      <Card>
        <div className="text-center py-2">
          <div className="w-24 h-24 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center">
            <Settings className="w-12 h-12 text-blue-500 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            正在解析算子文件
          </h2>
          <p className="text-gray-600 mb-8">
            系统正在自动分析您的算子文件，提取配置信息...
          </p>

          {/* 已上传文件列表 */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              已上传文件
            </h3>
            <div className="space-y-2">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-gray-500" />
                    <span className="font-medium">{file.name}</span>
                    <span className="text-sm text-gray-500">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
              ))}
            </div>
          </div>

          {/* 解析进度 */}
          <div className="max-w-md mx-auto">
            <Progress
              percent={parseProgress}
              status="active"
              strokeColor="#3B82F6"
            />
            <p className="mt-2 text-sm text-gray-600">
              解析进度: {parseProgress}%
            </p>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderConfigureStep = () => (
    <div className="w-full mx-auto ">
      {/* 解析结果 */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <h2 className="text-xl font-bold text-gray-900">解析完成</h2>
        </div>

        {parseError && (
          <Alert
            message="解析过程中发现问题"
            description={parseError}
            type="warning"
            showIcon
            className="mb-6"
          />
        )}

        {parsedInfo && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 基本信息 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">基本信息</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    算子名称
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.name}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    版本
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.version}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    作者
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.author}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    分类
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.category}
                  </div>
                </div>
              </div>
            </div>

            {/* 技术规格 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">技术规格</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    框架
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.framework}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    语言
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.language}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    类型
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.type}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    模态
                  </label>
                  <div className="p-2 bg-gray-50 rounded border text-gray-900">
                    {parsedInfo.modality.join(", ")}
                  </div>
                </div>
              </div>
            </div>

            {/* 描述 */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <div className="p-3 bg-gray-50 rounded border text-gray-900">
                {parsedInfo.description}
              </div>
            </div>

            {/* 依赖项 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                依赖项
              </label>
              <div className="p-3 bg-gray-50 rounded border">
                <div className="space-y-1">
                  {parsedInfo.dependencies.map((dep, index) => (
                    <div
                      key={index}
                      className="text-sm text-gray-900 font-mono"
                    >
                      {dep}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 性能指标 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                性能指标
              </label>
              <div className="p-3 bg-gray-50 rounded border space-y-2">
                {parsedInfo.performance.accuracy && (
                  <div className="text-sm">
                    <span className="font-medium">准确率:</span>{" "}
                    {parsedInfo.performance.accuracy}%
                  </div>
                )}
                <div className="text-sm">
                  <span className="font-medium">速度:</span>{" "}
                  {parsedInfo.performance.speed}
                </div>
                <div className="text-sm">
                  <span className="font-medium">内存:</span>{" "}
                  {parsedInfo.performance.memory}
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 标签配置 */}
      <Card>
        {/* 预定义标签 */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">推荐标签</h3>
          <div className="flex flex-wrap gap-2">
            {availableTags.map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  if (selectedTags.includes(tag)) {
                    handleRemoveTag(tag);
                  } else {
                    setSelectedTags([...selectedTags, tag]);
                  }
                }}
                className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                  selectedTags.includes(tag)
                    ? "bg-blue-100 text-blue-800 border-blue-200"
                    : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* 自定义标签 */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            添加自定义标签
          </h3>
          <div className="flex gap-2">
            <Input
              placeholder="输入自定义标签..."
              value={customTag}
              onChange={(e) => setCustomTag(e.target.value)}
              onPressEnter={handleAddCustomTag}
              className="flex-1"
            />
            <Button onClick={handleAddCustomTag} disabled={!customTag.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              添加
            </Button>
          </div>
        </div>

        {/* 已选标签 */}
        {selectedTags.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              已选标签 ({selectedTags.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {selectedTags.map((tag) => (
                <div
                  key={tag}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                >
                  <TagIcon className="w-3 h-3" />
                  <span>{tag}</span>
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 hover:text-blue-600"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-end gap-3 mt-8">
          <Button onClick={() => setUploadStep("upload")}>重新上传</Button>
          <Button onClick={() => setUploadStep("preview")}>预览</Button>
          <Button
            type="primary"
            onClick={handlePublish}
            disabled={selectedTags.length === 0}
          >
            发布算子
          </Button>
        </div>
      </Card>
    </div>
  );

  const renderPreviewStep = () => (
    <div className="max-w-4xl mx-auto">
      <Card>
        <div className="text-center py-2">
          <div className="w-24 h-24 mx-auto mb-6 bg-green-50 rounded-full flex items-center justify-center">
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">发布成功！</h2>
          <p className="text-gray-600 mb-8">您的算子已成功发布到算子市场</p>

          <div className="flex justify-center gap-4">
            <Button onClick={() => setUploadStep("upload")}>
              <Plus className="w-4 h-4 mr-2" />
              继续上传
            </Button>
            <Button type="primary">
              <Eye className="w-4 h-4 mr-2" />
              查看算子
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderStepIndicator = () => (
    <div className="mb-6">
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
  );

  return (
    <div className="min-h-screen">
      {renderStepIndicator()}
      {uploadStep === "upload" && renderUploadStep()}
      {uploadStep === "parsing" && renderParsingStep()}
      {uploadStep === "configure" && renderConfigureStep()}
      {uploadStep === "preview" && renderPreviewStep()}
    </div>
  );
}
