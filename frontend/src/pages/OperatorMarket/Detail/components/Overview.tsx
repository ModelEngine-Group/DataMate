import {DescriptionsProps, Card, Descriptions, Tag} from "antd";

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
  return (
    <div className="flex flex-col gap-4">
      {/* 基本信息 */}
      <Card>
        <Descriptions column={2} title="基本信息" items={descriptionItems} />
      </Card>

      <Card title="描述" styles={{header: {borderBottom: 'none'}}}>
        <p>{operator.description}</p>
      </Card>
    </div>
  );
}
