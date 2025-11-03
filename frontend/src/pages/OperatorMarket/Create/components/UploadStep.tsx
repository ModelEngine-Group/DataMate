import { Spin } from "antd";
import { Upload, FileText } from "lucide-react";

export default function UploadStep({ isUploading, onUpload }) {
  const supportedFormats = [
    { ext: ".py", desc: "Python 脚本文件" },
    { ext: ".zip", desc: "压缩包文件" },
    { ext: ".tar.gz", desc: "压缩包文件" },
    { ext: ".tar", desc: "压缩包文件" },
    { ext: ".whl", desc: "Python Wheel 包" },
    { ext: ".yaml", desc: "配置文件" },
    { ext: ".yml", desc: "配置文件" },
    { ext: ".json", desc: "JSON 配置文件" },
  ];

  return (
    <div className="py-2 w-full text-center">
      <div className="w-24 h-24 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center">
        <Upload className="w-12 h-12 text-blue-500" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">上传算子文件</h2>
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
            <div key={index} className="p-3 border border-gray-200 rounded-lg">
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
            onUpload(files);
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
              onUpload(files);
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
  );
}
