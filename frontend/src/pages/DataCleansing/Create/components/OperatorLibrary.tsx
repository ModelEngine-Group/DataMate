import React, {useEffect, useMemo, useState} from "react";
import {Button, Card, Checkbox, Collapse, Input, Select, Tag, Tooltip,} from "antd";
import {SearchOutlined, StarFilled, StarOutlined} from "@ant-design/icons";
import {CategoryI, OperatorI} from "@/pages/OperatorMarket/operator.model";
import {Layers} from "lucide-react";
import {updateOperatorByIdUsingPut} from "@/pages/OperatorMarket/operator.api.ts";

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

const handleStar = async (operator: OperatorI, toggleFavorite: (id: string) => void) => {
  const data = {
    id: operator.id,
    isStar: !operator.isStar
  };
  await updateOperatorByIdUsingPut(operator.id, data);
  toggleFavorite(operator.id)
}

const OperatorList: React.FC<OperatorListProps> = ({
  operators,
  favorites,
  toggleFavorite,
  toggleOperator,
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
            <span
              className="cursor-pointer"
              onClick={(event) => {
                  event.stopPropagation();
                  handleStar(operator, toggleFavorite);
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
  categoryOptions: CategoryI[];
  setSelectedOperators: (operators: OperatorI[]) => void;
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
  categoryOptions,
  setSelectedOperators,
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

    if (searchTerm) {
      Object.keys(groups).forEach((key) => {
        groups[key].operators = groups[key].operators.filter((operator) =>
          operator.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
        if (groups[key].operators.length === 0) {
          delete groups[key];
        }
      });
    }

    if (showFavorites) {
      Object.keys(groups).forEach((key) => {
        groups[key].operators = groups[key].operators.filter((operator) =>
          favorites.has(operator.id)
        );
        if (groups[key].operators.length === 0) {
          delete groups[key];
        }
      });
    }

    setExpandedCategories(new Set(Object.keys(groups)));
    return groups;
  }, [categoryOptions, selectedCategory, searchTerm, showFavorites]);

  // 过滤算子
  const filteredOperators = useMemo(() => {
    return Object.values(groupedOperators).flatMap(
      (category) => category.operators
    );
  }, [groupedOperators]);

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

  const fetchFavorite = async () => {
    const newFavorites = new Set(favorites);
    operatorList.forEach(item => {
      item.isStar && newFavorites.add(item.id);
    });
    setFavorites(newFavorites);
  }

  useEffect(() => {
    fetchFavorite()
  }, [operatorList]);

  // 全选分类算子
  const handleSelectAll = (operators: OperatorI[]) => {
    const newSelected = [...selectedOperators];
    operators.forEach((operator) => {
      if (!newSelected.some((op) => op.id === operator.id)) {
        newSelected.push(operator);
      }
    });
    setSelectedOperators(newSelected);
  };

  return (
    <div className="w-1/4 h-full min-w-3xs flex flex-col">
      <div className="pb-4 border-b border-gray-200">
        <span className="flex items-center font-semibold text-base">
          <Layers className="w-4 h-4 mr-2" />
          算子库({filteredOperators.length})
        </span>
      </div>
      <div className="flex flex-col h-full pt-4 pr-4 overflow-hidden">
        {/* 过滤器 */}
        <div className="flex flex-wrap gap-2 border-b border-gray-100 pb-4">
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索算子名称..."
            value={searchTerm}
            allowClear
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
                  <div className="flex items-center justify-between w-full">
                    <span className="flex items-center gap-2">
                      <span>{category.name}</span>
                      <Tag>{category.operators.length}</Tag>
                    </span>
                    <Button
                      type="link"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectAll(category.operators);
                      }}
                    >
                      全选
                    </Button>
                  </div>
                }
              >
                <OperatorList
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
