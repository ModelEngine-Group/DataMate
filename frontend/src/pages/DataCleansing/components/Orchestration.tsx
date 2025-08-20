import type React from "react";
import { useState, useMemo } from "react";
import {
  Card,
  Button,
  Input,
  Select,
  Radio,
  Checkbox,
  Slider,
  Tag,
  Collapse,
  Divider,
  Tooltip,
} from "antd";
import {
  StarOutlined,
  StarFilled,
  SettingOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  FilterOutlined,
  BarChartOutlined,
  FileTextOutlined,
  SearchOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ThunderboltOutlined,
  PictureOutlined,
  CalculatorOutlined,
  ShareAltOutlined,
  ClusterOutlined,
  AimOutlined,
  SwapOutlined,
} from "@ant-design/icons";

// 算子分类
const OPERATOR_CATEGORIES = {
  data: { name: "数据清洗", icon: <DatabaseOutlined />, color: "#1677ff" },
  ml: { name: "机器学习", icon: <ThunderboltOutlined />, color: "#722ed1" },
  vision: { name: "计算机视觉", icon: <PictureOutlined />, color: "#52c41a" },
  nlp: { name: "自然语言处理", icon: <FileTextOutlined />, color: "#faad14" },
  analysis: { name: "数据分析", icon: <BarChartOutlined />, color: "#f5222d" },
  transform: { name: "数据转换", icon: <SwapOutlined />, color: "#13c2c2" },
  io: { name: "输入输出", icon: <FileTextOutlined />, color: "#595959" },
  math: { name: "数学计算", icon: <CalculatorOutlined />, color: "#fadb14" },
};

// 算子类型定义
interface OperatorTemplate {
  id: string;
  name: string;
  type: string;
  category: keyof typeof OPERATOR_CATEGORIES;
  icon: React.ReactNode;
  description: string;
  tags: string[];
  isPopular?: boolean;
  params: {
    [key: string]: {
      type: "input" | "select" | "radio" | "checkbox" | "range";
      label: string;
      value: any;
      options?: string[] | { label: string; value: any }[];
      min?: number;
      max?: number;
      step?: number;
    };
  };
}

interface OperatorConfig extends OperatorTemplate {
  id: string;
}

// 模拟算子模板
const generateOperatorTemplates = (): OperatorTemplate[] => {
  const templates: OperatorTemplate[] = [
    {
      id: "data_reader_mysql",
      name: "MySQL读取",
      type: "data_reader",
      category: "data",
      icon: <DatabaseOutlined />,
      description: "从MySQL数据库读取数据",
      tags: ["数据库", "读取", "MySQL"],
      isPopular: true,
      params: {
        host: { type: "input", label: "主机地址", value: "localhost" },
        port: { type: "input", label: "端口", value: "3306" },
        database: { type: "input", label: "数据库名", value: "" },
        table: { type: "input", label: "表名", value: "" },
        limit: {
          type: "range",
          label: "读取行数",
          value: [1000],
          min: 100,
          max: 10000,
          step: 100,
        },
      },
    },
    {
      id: "data_reader_csv",
      name: "CSV读取",
      type: "data_reader",
      category: "data",
      icon: <FileTextOutlined />,
      description: "读取CSV文件数据",
      tags: ["文件", "读取", "CSV"],
      isPopular: true,
      params: {
        filepath: { type: "input", label: "文件路径", value: "" },
        encoding: {
          type: "select",
          label: "编码",
          value: "utf-8",
          options: ["utf-8", "gbk", "ascii"],
        },
        delimiter: { type: "input", label: "分隔符", value: "," },
      },
    },
    {
      id: "data_filter",
      name: "数据过滤",
      type: "filter",
      category: "data",
      icon: <FilterOutlined />,
      description: "根据条件过滤数据行",
      tags: ["过滤", "条件", "筛选"],
      isPopular: true,
      params: {
        column: { type: "input", label: "过滤字段", value: "" },
        operator: {
          type: "select",
          label: "操作符",
          value: "equals",
          options: [
            "equals",
            "not_equals",
            "greater_than",
            "less_than",
            "contains",
          ],
        },
        value: { type: "input", label: "过滤值", value: "" },
      },
    },
    {
      id: "linear_regression",
      name: "线性回归",
      type: "ml_model",
      category: "ml",
      icon: <ThunderboltOutlined />,
      description: "训练线性回归模型",
      tags: ["回归", "监督学习", "预测"],
      isPopular: true,
      params: {
        features: {
          type: "checkbox",
          label: "特征列",
          value: [],
          options: ["feature1", "feature2", "feature3"],
        },
        target: { type: "input", label: "目标列", value: "" },
        test_size: {
          type: "range",
          label: "测试集比例",
          value: [0.2],
          min: 0.1,
          max: 0.5,
          step: 0.1,
        },
      },
    },
    {
      id: "random_forest",
      name: "随机森林",
      type: "ml_model",
      category: "ml",
      icon: <ClusterOutlined />,
      description: "训练随机森林模型",
      tags: ["分类", "回归", "集成学习"],
      params: {
        n_estimators: {
          type: "range",
          label: "树的数量",
          value: [100],
          min: 10,
          max: 500,
          step: 10,
        },
        max_depth: {
          type: "range",
          label: "最大深度",
          value: [10],
          min: 3,
          max: 20,
          step: 1,
        },
        features: {
          type: "checkbox",
          label: "特征列",
          value: [],
          options: ["feature1", "feature2", "feature3"],
        },
      },
    },
    {
      id: "image_resize",
      name: "图像缩放",
      type: "image_transform",
      category: "vision",
      icon: <PictureOutlined />,
      description: "调整图像尺寸",
      tags: ["图像", "缩放", "预处理"],
      params: {
        width: { type: "input", label: "宽度", value: "224" },
        height: { type: "input", label: "高度", value: "224" },
        method: {
          type: "select",
          label: "缩放方法",
          value: "bilinear",
          options: ["bilinear", "nearest", "bicubic"],
        },
      },
    },
    {
      id: "object_detection",
      name: "目标检测",
      type: "vision_model",
      category: "vision",
      icon: <AimOutlined />,
      description: "检测图像中的目标对象",
      tags: ["检测", "目标", "YOLO"],
      params: {
        model: {
          type: "select",
          label: "模型",
          value: "yolov5",
          options: ["yolov5", "yolov8", "rcnn"],
        },
        confidence: {
          type: "range",
          label: "置信度阈值",
          value: [0.5],
          min: 0.1,
          max: 1.0,
          step: 0.1,
        },
        classes: {
          type: "checkbox",
          label: "检测类别",
          value: [],
          options: ["person", "car", "dog", "cat"],
        },
      },
    },
  ];

  // 生成更多算子以模拟100+的场景
  const additionalTemplates: OperatorTemplate[] = [];
  const categories = Object.keys(
    OPERATOR_CATEGORIES
  ) as (keyof typeof OPERATOR_CATEGORIES)[];
  for (let i = 0; i < 95; i++) {
    const category = categories[i % categories.length];
    additionalTemplates.push({
      id: `operator_${i + 8}`,
      name: `算子${i + 8}`,
      type: `type_${i + 8}`,
      category,
      icon: <ThunderboltOutlined />,
      description: `这是第${i + 8}个算子的描述`,
      tags: [`标签${(i % 5) + 1}`, `功能${(i % 3) + 1}`],
      isPopular: i % 10 === 0,
      params: {
        param1: { type: "input", label: "参数1", value: "" },
        param2: {
          type: "select",
          label: "参数2",
          value: "option1",
          options: ["option1", "option2", "option3"],
        },
      },
    });
  }
  return [...templates, ...additionalTemplates];
};

const operatorTemplates = generateOperatorTemplates();

export default function Component({ handleAdd, handleRemove }) {
  const [operators, setOperators] = useState<OperatorConfig[]>([]);
  const [selectedOperator, setSelectedOperator] = useState<string | null>(null);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [showFavorites, setShowFavorites] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["data", "ml"])
  );
  const [editingIndex, setEditingIndex] = useState<string | null>(null);

  // 过滤算子
  const filteredTemplates = useMemo(() => {
    let filtered = operatorTemplates;
    if (searchTerm) {
      filtered = filtered.filter(
        (template) =>
          template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          template.description
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          template.tags.some((tag) =>
            tag.toLowerCase().includes(searchTerm.toLowerCase())
          )
      );
    }
    if (selectedCategory !== "all") {
      filtered = filtered.filter(
        (template) => template.category === selectedCategory
      );
    }
    if (showFavorites) {
      filtered = filtered.filter((template) => favorites.has(template.id));
    }
    return filtered;
  }, [searchTerm, selectedCategory, showFavorites, favorites]);

  // 按分类分组
  const groupedTemplates = useMemo(() => {
    const grouped: { [key: string]: OperatorTemplate[] } = {};
    filteredTemplates.forEach((template) => {
      if (!grouped[template.category]) {
        grouped[template.category] = [];
      }
      grouped[template.category].push(template);
    });
    return grouped;
  }, [filteredTemplates]);

  // 添加算子
  const addOperator = (template: OperatorTemplate) => {
    const newOperator: OperatorConfig = {
      ...template,
      id: `${template.id}_${Date.now()}`,
      params: JSON.parse(JSON.stringify(template.params)),
    };
    setOperators([...operators, newOperator]);
    handleAdd(newOperator);
  };

  // 删除算子
  const removeOperator = (id: string) => {
    setOperators(operators.filter((op) => op.id !== id));
    if (selectedOperator === id) setSelectedOperator(null);
    handleRemove(id);
  };

  // 更新算子参数
  const updateOperatorParam = (id: string, paramKey: string, value: any) => {
    setOperators(
      operators.map((op) =>
        op.id === id
          ? {
              ...op,
              params: {
                ...op.params,
                [paramKey]: {
                  ...op.params[paramKey],
                  value,
                },
              },
            }
          : op
      )
    );
  };

  // 收藏切换
  const toggleFavorite = (templateId: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(templateId)) {
      newFavorites.delete(templateId);
    } else {
      newFavorites.add(templateId);
    }
    setFavorites(newFavorites);
  };

  // 分类展开切换
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // 拖拽处理
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = "move";
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };
  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null) return;
    const newOperators = [...operators];
    const draggedOperator = newOperators[draggedIndex];
    newOperators.splice(draggedIndex, 1);
    newOperators.splice(dropIndex, 0, draggedOperator);
    setOperators(newOperators);
    setDraggedIndex(null);
  };
  // 从算子库拖拽到编排区
  const handleTemplateDragStart = (
    e: React.DragEvent,
    template: OperatorTemplate
  ) => {
    e.dataTransfer.setData("application/json", JSON.stringify(template));
    e.dataTransfer.effectAllowed = "copy";
  };

  // 渲染参数配置组件
  const renderParamConfig = (
    operator: OperatorConfig,
    paramKey: string,
    param: any
  ) => {
    const value = param.value;
    const updateValue = (newValue: any) =>
      updateOperatorParam(operator.id, paramKey, newValue);
    switch (param.type) {
      case "input":
        return (
          <FormItem label={param.label} key={paramKey}>
            <Input
              value={value}
              onChange={(e) => updateValue(e.target.value)}
              placeholder={`请输入${param.label}`}
            />
          </FormItem>
        );
      case "select":
        return (
          <FormItem label={param.label} key={paramKey}>
            <Select
              value={value}
              onChange={updateValue}
              options={(param.options || []).map((option: any) =>
                typeof option === "string"
                  ? { label: option, value: option }
                  : option
              )}
              placeholder={`请选择${param.label}`}
            />
          </FormItem>
        );
      case "radio":
        return (
          <FormItem label={param.label} key={paramKey}>
            <Radio.Group
              value={value}
              onChange={(e) => updateValue(e.target.value)}
            >
              {(param.options || []).map((option: any) => (
                <Radio
                  key={typeof option === "string" ? option : option.value}
                  value={typeof option === "string" ? option : option.value}
                >
                  {typeof option === "string" ? option : option.label}
                </Radio>
              ))}
            </Radio.Group>
          </FormItem>
        );
      case "checkbox":
        return (
          <FormItem label={param.label} key={paramKey}>
            <Checkbox.Group
              value={value}
              onChange={updateValue}
              options={param.options || []}
            />
          </FormItem>
        );
      case "range":
        return (
          <FormItem label={param.label} key={paramKey}>
            <Slider
              value={Array.isArray(value) ? value : [value]}
              onChange={updateValue}
              min={param.min || 0}
              max={param.max || 100}
              step={param.step || 1}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 12,
                color: "#888",
              }}
            >
              <span>{param.min || 0}</span>
              <span style={{ fontWeight: 500 }}>
                {Array.isArray(value) ? value[0] : value}
              </span>
              <span>{param.max || 100}</span>
            </div>
          </FormItem>
        );
      default:
        return null;
    }
  };

  const selectedOp = operators.find((op) => op.id === selectedOperator);
  const FormItem = ({ label, children, ...rest }: any) => (
    <div className="mb-4" {...rest}>
      <div className="mb-1 font-medium">{label}</div>
      {children}
    </div>
  );

  return (
    <div className="flex h-[800px] bg-[#fafbfc]">
      {/* 左侧算子库 */}
      <div className="w-80 flex flex-col border-r border-gray-200 bg-white">
        <div className="p-4 border-b border-gray-200">
          <div className="font-semibold flex items-center gap-2 mb-4">
            <AppstoreOutlined />
            算子库
            <Tag color="default" className="ml-auto">{operatorTemplates.length}</Tag>
          </div>
          {/* 搜索栏 */}
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索算子..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-3"
          />
          {/* 过滤器 */}
          <div className="flex gap-2 mb-3">
            <Select
              value={selectedCategory}
              onChange={setSelectedCategory}
              className="flex-1"
            >
              <Select.Option value="all">全部分类</Select.Option>
              {Object.entries(OPERATOR_CATEGORIES).map(([key, category]) => (
                <Select.Option key={key} value={key}>
                  <span className="flex items-center gap-1">
                    {category.icon}
                    {category.name}
                  </span>
                </Select.Option>
              ))}
            </Select>
            <Tooltip title="只看收藏">
              <Button
                type={showFavorites ? "default" : "dashed"}
                icon={
                  showFavorites ? (
                    <StarFilled className="text-yellow-400" />
                  ) : (
                    <StarOutlined />
                  )
                }
                onClick={() => setShowFavorites(!showFavorites)}
              />
            </Tooltip>
            <Tooltip title={viewMode === "grid" ? "切换为列表" : "切换为网格"}>
              <Button
                icon={
                  viewMode === "grid" ? (
                    <UnorderedListOutlined />
                  ) : (
                    <AppstoreOutlined />
                  )
                }
                onClick={() =>
                  setViewMode(viewMode === "grid" ? "list" : "grid")
                }
              />
            </Tooltip>
          </div>
        </div>
        {/* 算子列表 */}
        <div className="flex-1 overflow-auto p-4">
          {/* 热门算子 */}
          {!searchTerm && selectedCategory === "all" && !showFavorites && (
            <>
              <div className="font-medium mb-2">热门算子</div>
              <div className={viewMode === "grid" ? "grid grid-cols-1 gap-2" : "block"}>
                {operatorTemplates
                  .filter((t) => t.isPopular)
                  .slice(0, 4)
                  .map((template) => (
                    <Card
                      key={template.id}
                      hoverable
                      className="mb-2 cursor-pointer"
                      draggable
                      onDragStart={(e) => handleTemplateDragStart(e, template)}
                      onClick={() => addOperator(template)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span
                            className="w-2 h-2 rounded-full inline-block"
                            style={{
                              background:
                                OPERATOR_CATEGORIES[template.category].color,
                            }}
                          />
                          {template.icon}
                          <span className="font-medium text-sm truncate">{template.name}</span>
                        </div>
                        <Button
                          type="text"
                          icon={
                            favorites.has(template.id) ? (
                              <StarFilled className="text-yellow-400" />
                            ) : (
                              <StarOutlined />
                            )
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(template.id);
                          }}
                        />
                      </div>
                    </Card>
                  ))}
              </div>
              <Divider />
            </>
          )}
          {/* 分类算子 */}
          <Collapse
            bordered={false}
            activeKey={Array.from(expandedCategories)}
            onChange={(keys) =>
              setExpandedCategories(
                new Set(Array.isArray(keys) ? keys : [keys])
              )
            }
            expandIconPosition="left"
            className="bg-transparent"
          >
            {Object.entries(groupedTemplates).map(([category, templates]) => (
              <Collapse.Panel
                key={category}
                header={
                  <span className="flex items-center gap-2">
                    {
                      OPERATOR_CATEGORIES[
                        category as keyof typeof OPERATOR_CATEGORIES
                      ]?.icon
                    }
                    <span>
                      {
                        OPERATOR_CATEGORIES[
                          category as keyof typeof OPERATOR_CATEGORIES
                        ]?.name
                      }
                    </span>
                    <Tag color="default" className="ml-2">
                      {templates.length}
                    </Tag>
                  </span>
                }
              >
                <div className={viewMode === "grid" ? "grid grid-cols-1 gap-2" : "block"}>
                  {templates.map((template) => (
                    <Card
                      key={template.id}
                      hoverable
                      className="mb-2 cursor-pointer"
                      draggable
                      onDragStart={(e) => handleTemplateDragStart(e, template)}
                      onClick={() => addOperator(template)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          {template.icon}
                          <span className="font-medium text-sm truncate">{template.name}</span>
                          {template.isPopular && (
                            <Tag color="gold" className="text-xs ml-1">
                              热门
                            </Tag>
                          )}
                        </div>
                        <Button
                          type="text"
                          icon={
                            favorites.has(template.id) ? (
                              <StarFilled className="text-yellow-400" />
                            ) : (
                              <StarOutlined />
                            )
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(template.id);
                          }}
                        />
                      </div>
                    </Card>
                  ))}
                </div>
              </Collapse.Panel>
            ))}
          </Collapse>
          {filteredTemplates.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <SearchOutlined className="text-3xl mb-2 opacity-50" />
              <div>未找到匹配的算子</div>
            </div>
          )}
        </div>
      </div>

      {/* 中间算子编排区域 */}
      <div className="flex-1 flex flex-col">
        {/* 工具栏 */}
        <div className="p-4 border-b border-gray-200 bg-[#fafbfc]">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-base flex items-center gap-2">
              算子编排
              <Tag color="default">{operators.length}</Tag>
            </span>
            <div className="w-60">
              <Select placeholder="选择模板" className="w-full">
                {Object.entries(OPERATOR_CATEGORIES).map(([key, category]) => (
                  <Select.Option key={key} value={key}>
                    <span className="flex items-center gap-1">
                      {category.icon}
                      {category.name}
                    </span>
                  </Select.Option>
                ))}
              </Select>
            </div>
          </div>
        </div>
        {/* 编排区域 */}
        <div className="flex-1 overflow-auto p-4">
          {operators.length === 0 ? (
            <div className="text-center py-16 text-gray-400 border-2 border-dashed border-gray-100 rounded-lg">
              <ShareAltOutlined className="text-5xl mb-4 opacity-50" />
              <div className="text-lg font-medium mb-2">
                开始构建您的算子流程
              </div>
              <div className="text-sm">
                从左侧算子库拖拽算子到此处，或点击算子添加
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {operators.map((operator, index) => (
                <Card
                  key={operator.id}
                  className={`cursor-pointer ${selectedOperator === operator.id ? "border-2 border-blue-500 bg-blue-50" : ""}`}
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, index)}
                  onClick={() => setSelectedOperator(operator.id)}
                >
                  <div className="flex items-center gap-3">
                    {/* 可编辑编号 */}
                    <div className="flex items-center gap-1">
                      <ThunderboltOutlined className="text-gray-300" />
                      {editingIndex === operator.id ? (
                        <Input
                          type="number"
                          min={1}
                          max={operators.length}
                          defaultValue={index + 1}
                          className="w-10 h-6 text-xs text-center"
                          autoFocus
                          onBlur={(e) =>
                            handleIndexChange(operator.id, e.target.value)
                          }
                          onKeyDown={(e) => {
                            if (e.key === "Enter")
                              handleIndexChange(
                                operator.id,
                                (e.target as HTMLInputElement).value
                              );
                            else if (e.key === "Escape") setEditingIndex(null);
                          }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <Tag
                          color="default"
                          className="cursor-pointer min-w-[24px] text-center"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingIndex(operator.id);
                          }}
                        >
                          {index + 1}
                        </Tag>
                      )}
                    </div>
                    {/* 分类颜色标识 */}
                    <span
                      className="w-2 h-2 rounded-full inline-block"
                      style={{
                        background:
                          OPERATOR_CATEGORIES[operator.category].color,
                      }}
                    />
                    {/* 算子图标和名称 */}
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {operator.icon}
                      <span className="font-medium text-sm truncate">
                        {operator.name}
                      </span>
                    </div>
                    {/* 分类标签 */}
                    <Tag color="default">
                      {OPERATOR_CATEGORIES[operator.category].name}
                    </Tag>
                    {/* 参数状态指示 */}
                    {Object.values(operator.params).some(
                      (param) =>
                        (param.type === "input" && !param.value) ||
                        (param.type === "checkbox" &&
                          Array.isArray(param.value) &&
                          param.value.length === 0)
                    ) && <Tag color="red">待配置</Tag>}
                    {/* 操作按钮 */}
                    <div className="flex gap-1">
                      <Button
                        type="text"
                        icon={<SettingOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedOperator(operator.id);
                        }}
                      />
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          removeOperator(operator.id);
                        }}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 右侧参数配置面板 */}
      <div className="w-80 flex flex-col border-l border-gray-200 bg-white">
        <div className="p-4 border-b border-gray-200">
          <span className="font-semibold flex items-center gap-2">
            <SettingOutlined />
            参数配置
          </span>
        </div>
        <div className="flex-1 overflow-auto p-4">
          {selectedOp ? (
            <div>
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2 h-2 rounded-full inline-block"
                    style={{
                      background:
                        OPERATOR_CATEGORIES[selectedOp.category].color,
                    }}
                  />
                  {selectedOp.icon}
                  <span className="font-medium">{selectedOp.name}</span>
                </div>
                <div className="text-sm text-gray-500">
                  {selectedOp.description}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedOp.tags.map((tag) => (
                    <Tag key={tag} color="default">
                      {tag}
                    </Tag>
                  ))}
                </div>
              </div>
              <Divider />
              <div>
                {Object.entries(selectedOp.params).map(([key, param]) =>
                  renderParamConfig(selectedOp, key, param)
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <SettingOutlined className="text-5xl mb-4 opacity-50" />
              <div>请选择一个算子进行参数配置</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
