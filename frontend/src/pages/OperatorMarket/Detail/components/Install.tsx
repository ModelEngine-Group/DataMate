import { Card, Button } from "antd";
import { Copy } from "lucide-react";

export default function renderInstallTab({ operator }) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加提示消息
  };
  return (
    <div className="flex flex-col gap-4">
      {/* 安装命令 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">安装命令</h3>
        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
          <div className="flex items-center justify-between">
            <span>{operator.installCommand}</span>
            <Button
              size="small"
              onClick={() => copyToClipboard(operator.installCommand)}
              className="ml-2"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* 系统要求 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">系统要求</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">Python 版本</span>
            <span className="text-gray-900">
              {operator.systemRequirements.python}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">内存要求</span>
            <span className="text-gray-900">
              {operator.systemRequirements.memory}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">存储空间</span>
            <span className="text-gray-900">
              {operator.systemRequirements.storage}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="font-medium text-gray-700">GPU 支持</span>
            <span className="text-gray-900">
              {operator.systemRequirements.gpu}
            </span>
          </div>
        </div>
      </Card>

      {/* 依赖项 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">依赖项</h3>
        <div className="space-y-2">
          {operator.dependencies.map((dep, index) => (
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

      {/* 快速开始 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">快速开始</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">1. 安装算子</h4>
            <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm">
              {operator.installCommand}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">2. 导入并使用</h4>
            <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm">
              {`from image_preprocessor import ImagePreprocessor
processor = ImagePreprocessor()
result = processor.process(image)`}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">3. 查看结果</h4>
            <p className="text-gray-600">
              处理后的图像将保存在指定路径，可以直接用于后续的机器学习任务。
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
