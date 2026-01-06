import { Card } from "antd";
import { Badge, ChevronRight } from "lucide-react";

export default function ChangeLog({ operator }) {
  const changelog = [
      {
        version: "1.2.0",
        date: "2024-01-23",
        changes: ["新增批量处理功能", "优化内存使用，减少50%内存占用", "添加GPU加速支持", "修复旋转操作的边界问题"],
      },
      {
        version: "1.1.0",
        date: "2024-01-10",
        changes: ["添加颜色空间转换功能", "支持WebP格式", "改进错误处理机制", "更新文档和示例"],
      },
      {
        version: "1.0.0",
        date: "2024-01-01",
        changes: ["首次发布", "支持基本图像预处理操作", "包含缩放、裁剪、旋转功能"],
      },
    ];

  return (
    <div className="flex flex-col gap-4">
      {changelog.map((version, index) => (
        <Card key={index}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                版本 {version.version}
              </h3>
              <p className="text-sm text-gray-600">{version.date}</p>
            </div>
            {index === 0 && (
              <Badge className="bg-blue-100 text-blue-800 border border-blue-200">
                最新版本
              </Badge>
            )}
          </div>
          <ul className="space-y-2">
            {version.changes.map((change, changeIndex) => (
              <li key={changeIndex} className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{change}</span>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
