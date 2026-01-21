import {DescriptionsProps, Card, Descriptions, Tag} from "antd";
import {FileExtensionMap, MediaType} from "@/pages/OperatorMarket/operator.const.tsx";

export default function Overview({ operator }) {
  const descriptionItems: DescriptionsProps["items"] = [
    {
      key: "version",
      label: "版本",
      children: operator.version,
    },
    {
      key: "category",
      label: "分类",
      children: (
        <div className="flex flex-wrap gap-2">
          {operator.categories.map((category, index) => (
            <Tag
              key={index}
              className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full"
            >
              {category}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      key: "inputs",
      label: "输入类型",
      children: operator.inputs,
    },
    {
      key: "createdAt",
      label: "创建时间",
      children: operator.createdAt,
    },
    {
      key: "outputs",
      label: "输出类型",
      children: operator.outputs,
    },
    {
      key: "lastModified",
      label: "最后修改",
      children: operator.updatedAt,
    },
  ];

  const tags = ["图像处理", "预处理", "缩放", "裁剪", "旋转", "计算机视觉", "深度学习"];

  const performance = {
    accuracy: 99.5,
    speed: "50ms/image",
    memory: "128MB",
    throughput: "20 images/sec",
  };

  return (
    <div className="flex flex-col gap-4">
      {/* 基本信息 */}
      <Card>
        <Descriptions column={2} title="基本信息" items={descriptionItems} />
      </Card>

      <Card title="描述" styles={{header: {borderBottom: 'none'}}}>
        <p>{operator.description}</p>
      </Card>

      {/* 标签 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">标签</h3>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, index) => (
            <Tag key={index} className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
              {tag}
            </Tag>
          ))}
        </div>
      </Card>

      {/* 性能指标 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">性能指标</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {performance.accuracy && (
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{performance.accuracy}%</div>
              <div className="text-sm text-gray-600">准确率</div>
            </div>
          )}
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{performance.speed}</div>
            <div className="text-sm text-gray-600">处理速度</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{performance.memory}</div>
            <div className="text-sm text-gray-600">内存使用</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{performance.throughput}</div>
            <div className="text-sm text-gray-600">吞吐量</div>
          </div>
        </div>
      </Card>

      {/* 输入输出格式 */}
      {operator.categories?.includes('系统预置') && (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">支持格式</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">输入格式</h4>
            <div className="flex flex-wrap gap-2">
              {FileExtensionMap[operator.inputs as MediaType].map((format, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-sm"
                >
                  {format}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">输出格式</h4>
            <div className="flex flex-wrap gap-2">
              {FileExtensionMap[operator.outputs as MediaType].map((format, index) => (
                <span key={index} className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded text-sm">
                  {format}
                </span>
              ))}
            </div>
          </div>
        </div>
      </Card>
      )}
    </div>
  );
}
