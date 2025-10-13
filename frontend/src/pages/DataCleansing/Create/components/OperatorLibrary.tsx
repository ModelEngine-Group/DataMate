import React, { useMemo, useState } from "react";
import {
  Card,
  Input,
  Select,
  Tooltip,
  Divider,
  Collapse,
  Tag,
  Checkbox,
} from "antd";
import { StarFilled, StarOutlined, SearchOutlined } from "@ant-design/icons";
import type { OperatorI } from "@/pages/DataCleansing/cleansing.model";

interface OperatorListProps {
  operators: OperatorI[];
  favorites: Set<string>;
  showPoppular?: boolean;
  toggleFavorite: (id: string) => void;
  toggleOperator: (operator: OperatorI) => void;
  selectedOperators: OperatorI[];
  onDragOperator: (
    e: React.DragEvent,
    item: OperatorI,
    source: "library"
  ) => void;
}

const OperatorList: React.FC<OperatorListProps> = ({
  operators,
  favorites,
  toggleFavorite,
  toggleOperator,
  showPoppular,
  selectedOperators,
  onDragOperator,
}) => (
  <div className="grid grid-cols-1 gap-2">
    {operators.map((operator) => {
      // 判断是否已选
      const isSelected = selectedOperators.some(
        (op) => op.originalId === operator.id
      );
      return (
        <Card
          size="small"
          key={operator.id}
          draggable
          hoverable
          onDragStart={(e) => onDragOperator(e, operator, "library")}
          onClick={() => toggleOperator(operator)}
        >
          <div className="flex items-center justify-between">
            <div className="flex flex-1 min-w-0 items-center gap-2">
              <Checkbox checked={isSelected} />
              <span className="flex-1 min-w-0 font-medium text-sm overflow-hidden text-ellipsis whitespace-nowrap">
                {operator.name}
              </span>
            </div>
            {showPoppular && operator.isStar && (
              <Tag color="gold" className="text-xs">
                热门
              </Tag>
            )}
            <span
              className="cursor-pointer"
              onClick={(e) => {
                e.stopPropagation();
                toggleFavorite(operator.id);
              }}
            >
              {favorites.has(operator.id) ? (
                <StarFilled style={{ color: "#FFD700" }} />
              ) : (
                <StarOutlined />
              )}
            </span>
          </div>
        </Card>
      );
    })}
  </div>
);

interface OperatorLibraryProps {
  operators: OperatorI[];
  operatorList: OperatorI[];
  OPERATOR_CATEGORIES: any;
  toggleOperator: (template: OperatorI) => void;
  handleDragStart: (
    e: React.DragEvent,
    item: OperatorI,
    source: "library"
  ) => void;
}

const OperatorLibrary: React.FC<OperatorLibraryProps> = ({
  operators,
  operatorList,
  OPERATOR_CATEGORIES,
  toggleOperator,
  handleDragStart,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [showFavorites, setShowFavorites] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["data", "ml"])
  );

  // 过滤算子
  const filteredTemplates = useMemo(() => {
    let filtered = operatorList;
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
  }, [operatorList, searchTerm, selectedCategory, showFavorites, favorites]);

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

  return (
    <div className="w-1/4 h-screen flex flex-col">
      <div className="pb-4 border-b border-gray-200">
        <span className="font-semibold text-base">
          算子库({operatorList.length})
        </span>
      </div>
      <div className="flex flex-col h-full pt-4 pr-4 overflow-hidden">
        {/* 过滤器 */}
        <div className="flex items-center gap-2 pb-4 border-b border-gray-100">
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索算子..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
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
            <span
              className="cursor-pointer"
              onClick={() => setShowFavorites(!showFavorites)}
            >
              {showFavorites ? (
                <StarFilled style={{ color: "#FFD700" }} />
              ) : (
                <StarOutlined />
              )}
            </span>
          </Tooltip>
        </div>
        {/* 算子列表 */}
        <div className="flex-1 overflow-auto pt-4">
          {/* 热门算子 */}
          {!searchTerm && selectedCategory === "all" && !showFavorites && (
            <div className="pr-4">
              <div className="font-medium mb-2">热门算子</div>
              <OperatorList
                operators={operatorList.filter((t) => t.isStar).slice(0, 4)}
                favorites={favorites}
                onDragOperator={handleDragStart}
                toggleOperator={toggleOperator}
                selectedOperators={operators}
                toggleFavorite={toggleFavorite}
              />
              <Divider />
            </div>
          )}
          {/* 分类算子 */}
          <Collapse
            ghost
            activeKey={Array.from(expandedCategories)}
            onChange={(keys) =>
              setExpandedCategories(
                new Set(Array.isArray(keys) ? keys : [keys])
              )
            }
          >
            {Object.entries(groupedTemplates).map(([category, templates]) => (
              <Collapse.Panel
                key={category}
                header={
                  <span className="flex items-center gap-2">
                    <span>
                      {
                        OPERATOR_CATEGORIES[
                          category as keyof typeof OPERATOR_CATEGORIES
                        ]?.name
                      }
                    </span>
                    <Tag>{templates.length}</Tag>
                  </span>
                }
              >
                <OperatorList
                  showPoppular
                  selectedOperators={operators}
                  operators={templates}
                  favorites={favorites}
                  toggleOperator={toggleOperator}
                  onDragOperator={handleDragStart}
                  toggleFavorite={toggleFavorite}
                />
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
    </div>
  );
};
export default OperatorLibrary;
