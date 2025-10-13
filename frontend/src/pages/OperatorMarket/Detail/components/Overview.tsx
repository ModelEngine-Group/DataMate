import { DescriptionsProps, Card, Descriptions, Tag } from "antd";
import { FileText, ImageIcon, Music, Video } from "lucide-react";

export default function Overview({ operator }) {
  const getModalityIcon = (modality: string) => {
    const iconMap = {
      text: FileText,
      image: ImageIcon,
      audio: Music,
      video: Video,
    };
    const IconComponent = iconMap[modality as keyof typeof iconMap] || FileText;
    return <IconComponent className="w-4 h-4" />;
  };

  const descriptionItems: DescriptionsProps["items"] = [
    {
      key: "version",
      label: "版本",
      children: operator.version,
    },
    {
      key: "category",
      label: "分类",
      children: operator.category,
    },
    {
      key: "language",
      label: "语言",
      children: operator.language,
    },
    {
      key: "modality",
      label: "模态",
      children: (
        <div className="flex items-center gap-2">
          {operator.modality.map((mod, index) => (
            <span
              key={index}
              className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
            >
              {getModalityIcon(mod)}
              {mod}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "framework",
      label: "框架",
      children: operator.framework,
    },
    {
      key: "type",
      label: "类型",
      children: operator.type,
    },
    {
      key: "size",
      label: "大小",
      children: operator.size,
    },
    {
      key: "license",
      label: "许可证",
      children: operator.license,
    },
    {
      key: "createdAt",
      label: "创建时间",
      children: operator.createdAt,
    },
    {
      key: "lastModified",
      label: "最后修改",
      children: operator.lastModified,
    },
  ];
  return (
    <div className="flex flex-col gap-4">
      {/* 基本信息 */}
      <Card>
        <Descriptions column={2} title="基本信息" items={descriptionItems} />
      </Card>

      {/* 标签 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">标签</h3>
        <div className="flex flex-wrap gap-2">
          {operator.tags.map((tag, index) => (
            <Tag
              key={index}
              className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full"
            >
              {tag}
            </Tag>
          ))}
        </div>
      </Card>

      {/* 性能指标 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">性能指标</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {operator.performance.accuracy && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {operator.performance.accuracy}%
              </div>
              <div className="text-sm text-gray-600">准确率</div>
            </div>
          )}
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {operator.performance.speed}
            </div>
            <div className="text-sm text-gray-600">处理速度</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {operator.performance.memory}
            </div>
            <div className="text-sm text-gray-600">内存使用</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {operator.performance.throughput}
            </div>
            <div className="text-sm text-gray-600">吞吐量</div>
          </div>
        </div>
      </Card>

      {/* 输入输出格式 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">支持格式</h3>
        <Descriptions column={2} bordered size="middle">
          <Descriptions.Item label="输入格式">
            <div className="flex flex-wrap gap-2">
              {operator.inputFormat.map((format, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-sm"
                >
                  .{format}
                </span>
              ))}
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="输出格式">
            <div className="flex flex-wrap gap-2">
              {operator.outputFormat.map((format, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded text-sm"
                >
                  .{format}
                </span>
              ))}
            </div>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
