import { Alert, Input, Form } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect } from "react";

export default function ConfigureStep({
  parsedInfo,
  parseError,
  setParsedInfo,
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(parsedInfo);
  }, [parsedInfo]);

  return (
    <>
      {/* 解析结果 */}
      {parseError && (
        <div className="mb-4">
          <Alert
            message="解析过程中发现问题"
            description={parseError}
            type="error"
            showIcon
          />
        </div>
      )}

      {!parseError && parsedInfo && (
        <Form
          form={form}
          layout="vertical"
          initialValues={parsedInfo}
          onValuesChange={(_, allValues) => {
            setParsedInfo({ ...parsedInfo, ...allValues });
          }}
        >
          {/* 基本信息 */}
          <h3 className="text-lg font-semibold text-gray-900">基本信息</h3>
          <Form.Item label="ID" name="id" rules={[{ required: true }]}>
            <Input value={parsedInfo.id} readOnly />
          </Form.Item>
          <Form.Item label="名称" name="name" rules={[{ required: true }]}>
            <Input value={parsedInfo.name} />
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{ required: true }]}>
            <Input value={parsedInfo.version} />
          </Form.Item>
          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: false }]}
          >
            <TextArea value={parsedInfo.description} />
          </Form.Item>

          <h3 className="text-lg font-semibold text-gray-900 mt-10 mb-2">
            应用示例
          </h3>
          <div className="border p-4 rounded-lg flex items-center justify-between gap-4">
            <div className="flex-1">
              <span className="bg-[#2196f3] border-radius px-4 py-1 rounded-tl-lg rounded-br-lg text-white">
                输入
              </span>
              <pre className="p-4 text-sm overflow-auto">
                {parsedInfo.inputs}
              </pre>
            </div>
            <h1 className="text-3xl">VS</h1>
            <div className="flex-1">
              <span className="bg-[#4caf50] border-radius px-4 py-1 rounded-tl-lg rounded-br-lg text-white">
                输出
              </span>
              <pre className=" p-4 text-sm overflow-auto">
                {parsedInfo.outputs}
              </pre>
            </div>
          </div>

          {/* <h3 className="text-lg font-semibold text-gray-900 mt-8">高级配置</h3> */}
        </Form>
      )}
    </>
  );
}
