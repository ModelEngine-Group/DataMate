import { Alert, Input, Form } from "antd";
import TextArea from "antd/es/input/TextArea";
import React, { useEffect } from "react";
import ParamConfig from "@/pages/DataCleansing/Create/components/ParamConfig.tsx";
import { ChevronRight, Plus, Trash2 } from "lucide-react";
import {MetricI} from "@/pages/OperatorMarket/operator.model.ts";

export default function ConfigureStep({
  parsedInfo,
  parseError,
  setParsedInfo,
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(parsedInfo);
  }, [parsedInfo]);

  const handleConfigChange = (
    operatorId: string,
    paramKey: string,
    value: any
  ) => {
    setParsedInfo((op) =>
      op.id === operatorId
        ? {
            ...op,
            overrides: {
              ...(op?.overrides || op?.defaultParams),
              [paramKey]: value,
            },
          }
        : op
    );
  };

  // 1. 【核心逻辑】处理输入框变化
  const handleChangelogChange = (changeIndex: number, newValue: string) => {
    const newParsedInfo = { ...parsedInfo };
    // 确保 releases[0] 存在
    if (newParsedInfo.releases && newParsedInfo.releases.length > 0) {
      newParsedInfo.releases[0].changelog[changeIndex] = newValue;
      setParsedInfo(newParsedInfo);
    }
  };

  // 2. 【辅助逻辑】删除某一行 (可选功能)
  const handleDeleteChange = (changeIndex: number) => {
    const newParsedInfo = { ...parsedInfo };
    if (newParsedInfo.releases && newParsedInfo.releases.length > 0) {
      newParsedInfo.releases[0].changelog.splice(changeIndex, 1);
      setParsedInfo(newParsedInfo);
    }
  };

  // 3. 【辅助逻辑】新增一行 (可选功能)
  const handleAddChange = () => {
    const newParsedInfo = { ...parsedInfo };
    if (!newParsedInfo.releases) newParsedInfo.releases = [];
    if (newParsedInfo.releases.length === 0) {
      // 如果没有 release，创建一个空的结构
      newParsedInfo.releases.push({ changelog: [] });
    }
    console.log(newParsedInfo);
    newParsedInfo.releases[0].changelog.push("");
    setParsedInfo(newParsedInfo);
  };

  const safeParse = (meta: unknown): unknown => {
    if (typeof meta === "string") {
      try {
        return JSON.parse(meta);
      } catch {
        return meta; // 保持原样
      }
    }
    return meta;
  };

  const metrics = safeParse(parsedInfo.metrics);

  return (
    <div className="p-2">
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
          <Form.Item
            label="输入类型"
            name="inputs"
            rules={[{ required: true }]}
          >
            <Input value={parsedInfo.inputs} />
          </Form.Item>
          <Form.Item
            label="输出类型"
            name="outputs"
            rules={[{ required: true }]}
          >
            <Input value={parsedInfo.outputs} />
          </Form.Item>

          <>
            <h3 className="text-lg font-semibold text-gray-900 mt-10 mb-2">
              更新日志
            </h3>
            {parsedInfo?.releases?.[0].changelog?.length == 0 ? (
              <div className="text-gray-500 text-sm py-4 text-center bg-gray-50 rounded-lg border border-dashed border-gray-300">
                暂无版本发布信息
                <button onClick={handleAddChange} className="ml-2 text-blue-600 hover:underline">
                  点击初始化
                </button>
              </div>
            ) : (
              <ul className="space-y-2">
                {/* 增加空数组保护：(currentRelease.changelog || []) */}
                {(parsedInfo?.releases?.[0].changelog || []).map((change, changeIndex) => (
                  <li key={changeIndex} className="group flex items-start gap-2 hover:bg-gray-50 p-1 rounded transition-colors">
                    <ChevronRight className="w-4 h-4 text-gray-400 mt-2.5 flex-shrink-0" />

                    {/* 可编辑的输入框 */}
                    <textarea
                      value={change}
                      onChange={(e) => handleChangelogChange(changeIndex, e.target.value)}
                      className="flex-1 bg-transparent border-transparent focus:border-blue-300 focus:ring-2 focus:ring-blue-100 rounded leading-relaxed resize-none overflow-hidden"
                      rows={1}
                      // 一个小技巧：自动调整高度（如果需要）可以加 auto-resize 逻辑，或者简单设为 textarea
                      style={{ minHeight: '32px', paddingTop: '6px' }}
                    />

                    {/* 删除按钮 (鼠标悬停时显示) */}
                    <button
                      onClick={() => handleDeleteChange(changeIndex)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                      title="删除此行"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </li>
                ))}

                <button
                  onClick={handleAddChange}
                  className="w-full py-2 flex items-center justify-center gap-2 border border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:text-blue-600 hover:border-blue-400 hover:bg-blue-50 transition-all group"
                >
                  <div className="bg-gray-100 group-hover:bg-blue-100 rounded-full p-0.5">
                    <Plus className="w-4 h-4" />
                  </div>
                  添加一行更新日志
                </button>
              </ul>
            )}
          </>

          {/* 性能指标 */}
          {metrics?.length > 0 && (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mt-10 mb-2">性能指标</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {metrics.map((item: MetricI, index) => (
                  <div
                    key={index}
                    className="text-center p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="text-2xl font-bold text-gray-900">
                      {item.metric}
                    </div>
                    <div className="text-sm text-gray-600">
                      {item.name}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {parsedInfo.configs && Object.keys(parsedInfo.configs).length > 0 && (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mt-10 mb-2">
                高级配置
              </h3>
              <Form layout="vertical">
                {Object.entries(parsedInfo?.configs).map(([key, param]) => (
                  <ParamConfig
                    key={key}
                    operator={parsedInfo}
                    paramKey={key}
                    param={param}
                    onParamChange={handleConfigChange}
                  />
                ))}
              </Form>
            </>
          )}
        </Form>
      )}
    </div>
  );
}
