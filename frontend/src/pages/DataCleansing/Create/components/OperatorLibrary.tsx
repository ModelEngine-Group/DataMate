import React, { useEffect, useMemo, useState } from "react";
import { Card, Input, Select, Tooltip, Collapse, Tag, Checkbox } from "antd";
import { StarFilled, StarOutlined, SearchOutlined } from "@ant-design/icons";
import type { OperatorI } from "@/pages/DataCleansing/cleansing.model";
import {
  queryCategoryTreeUsingGet,
  queryOperatorsUsingPost,
} from "@/pages/OperatorMarket/operator.api";

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
      const isSelected = selectedOperators.some((op) => op.id === operator.id);
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
  selectedOperators: OperatorI[];
  operatorList: OperatorI[];
  toggleOperator: (template: OperatorI) => void;
  handleDragStart: (
    e: React.DragEvent,
    item: OperatorI,
    source: "library"
  ) => void;
}

const OperatorLibrary: React.FC<OperatorLibraryProps> = ({
  selectedOperators,
  operatorList,
  toggleOperator,
  handleDragStart,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [showFavorites, setShowFavorites] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set([])
  );
  const [categoryOptions, setCategoryOptions] = useState([]);

  const initData = async () => {
    const [categoryRes, operatorRes] = await Promise.all([
      queryCategoryTreeUsingGet(),
      queryOperatorsUsingPost({ page: 0, size: 1000 }),
    ]);
    const options = categoryRes.data.reduce((acc: any[], item: any) => {
      const cats = item.categories.map((cat) => ({
        ...cat,
        type: item.name,
        label: cat.name,
        value: cat.id,
        icon: cat.icon,
        operators: operatorRes.data.content.filter(
          (op) => op[item.name] === cat.name
        ),
      }));
      acc.push(...cats);
      return acc;
    }, [] as { id: string; name: string; icon: React.ReactNode }[]);

    setCategoryOptions(options);
  };

  useEffect(() => {
    initData();
  }, []);

  // 按分类分组
  const groupedOperators = useMemo(() => {
    const groups: { [key: string]: OperatorI[] } = {};
    categoryOptions.forEach((cat: any) => {
      groups[cat.name] = {
        ...cat,
        operators: operatorList.filter((op) => op.categories?.includes(cat.id)),
      };
    });

    if (selectedCategory && selectedCategory !== "all") {
      Object.keys(groups).forEach((key) => {
        if (groups[key].id !== selectedCategory) {
          delete groups[key];
        }
      });
    }
    setExpandedCategories(new Set(Object.keys(groups)));
    return groups;
  }, [categoryOptions, selectedCategory]);

  // 过滤算子
  const filteredOperators = useMemo(() => {
    let filtered = operatorList;
    if (searchTerm) {
      filtered = filtered.filter(
        (operator) =>
          operator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          operator.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    if (showFavorites) {
      filtered = filtered.filter((operator) => favorites.has(operator.id));
    }
    return filtered;
  }, [groupedOperators, searchTerm, showFavorites, favorites]);

  // 收藏切换
  const toggleFavorite = (operatorId: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(operatorId)) {
      newFavorites.delete(operatorId);
    } else {
      newFavorites.add(operatorId);
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
        <div className="flex gap-2 border-b border-gray-100">
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索算子..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Select
            value={selectedCategory}
            options={[{ label: "全部分类", value: "all" }, ...categoryOptions]}
            onChange={setSelectedCategory}
            className="flex-1"
            placeholder="选择分类"
          ></Select>
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
        <div className="flex-1 overflow-auto">
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
            {Object.entries(groupedOperators).map(([key, category]) => (
              <Collapse.Panel
                key={key}
                header={
                  <span className="flex items-center gap-2">
                    <span>{category.name}</span>
                    <Tag>{category.operators.length}</Tag>
                  </span>
                }
              >
                <OperatorList
                  showPoppular
                  selectedOperators={selectedOperators}
                  operators={category.operators}
                  favorites={favorites}
                  toggleOperator={toggleOperator}
                  onDragOperator={handleDragStart}
                  toggleFavorite={toggleFavorite}
                />
              </Collapse.Panel>
            ))}
          </Collapse>
          {filteredOperators.length === 0 && (
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
