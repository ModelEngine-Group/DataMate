import { Card, Button } from "antd";
import { Copy } from "lucide-react";

export default function Requirement({ operator }) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加提示消息
  };

  let requirement = [];
  try {
    requirement = JSON.parse(operator.runtime || "{}");
  } catch (e) {
    console.error("数据解析失败", e);
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 系统要求 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">系统要求</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">CPU要求</span>
            <span className="text-gray-900">
              {requirement?.cpu || '无限制'}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">内存要求</span>
            <span className="text-gray-900">
              {requirement?.memory || "无限制"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">存储空间</span>
            <span className="text-gray-900">
              {requirement?.storage || "无限制"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">GPU 支持</span>
            <span className="text-gray-900">
              {requirement?.gpu > 0 ? "是" : "否"}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="font-medium text-gray-700">NPU 支持</span>
            <span className="text-gray-900">
              {requirement?.npu > 0 ? "是" : "否" }
            </span>
          </div>
        </div>
      </Card>

      {/* 依赖项 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">依赖项</h3>
        <div className="space-y-2">
          {operator.requirements?.map((dep, index) => (
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
