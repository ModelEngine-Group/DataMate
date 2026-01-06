import { Card, Button } from "antd";
import { Copy } from "lucide-react";

export default function Requirement({ operator }) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加提示消息
  };

  const dependencies = ["opencv-python>=4.5.0", "pillow>=8.0.0", "numpy>=1.20.0", "torch>=1.9.0", "torchvision>=0.10.0"];

  return (
    <div className="flex flex-col gap-4">
      {/* 系统要求 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">系统要求</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">内存要求</span>
            <span className="text-gray-900">
              {operator.runtime?.memory || ">=1GB RAM"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">存储空间</span>
            <span className="text-gray-900">
              {operator.runtime?.storage || ">=10MB"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">GPU 支持</span>
            <span className="text-gray-900">
              {operator.runtime?.gpu || "Optional (CUDA support)"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="font-medium text-gray-700">NPU 支持</span>
            <span className="text-gray-900">
              {operator.runtime?.npu || "Optional (Ascend support)"}
            </span>
          </div>
        </div>
      </Card>

      {/* 依赖项 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">依赖项</h3>
        <div className="space-y-2">
          {dependencies?.map((dep, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span className="font-mono text-sm text-gray-900">{dep}</span>
              <Button size="small" onClick={() => copyToClipboard(dep)}>
                <Copy className="w-3 h-3" />
              </Button>
            </div>
          ))}
        </div>
      </Card>

    </div>
  );
}
