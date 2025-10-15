import { useState } from "react";
import { Button } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import {
  Plus,
  X,
  Code,
  Cpu,
  Brain,
  Zap,
  Settings,
  Package,
} from "lucide-react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import { mockOperators } from "@/mock/operator";
import type { Operator } from "@/pages/OperatorMarket/operator.model";
import Filters from "./components/Filters";
import TagManagement from "@/components/TagManagement";
import { ListView } from "./components/List";

export default function OperatorMarketPage() {
  const navigate = useNavigate();
  const [operators, setOperators] = useState<Operator[]>(mockOperators);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedModalities, setSelectedModalities] = useState<string[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showTagManager, setShowTagManager] = useState(false);

  const [showFilters, setShowFilters] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});
  const [sortBy, setSortBy] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const filterOptions = [
    {
      key: "tag",
      label: "标签",
      options: [
        { label: "免费", value: "free" },
        { label: "付费", value: "paid" },
      ],
    },
  ];

  const sortOptions = [
    { label: "最近修改", value: "lastModified" },
    { label: "创建时间", value: "createdAt" },
    { label: "名称", value: "name" },
    { label: "使用量", value: "usage" },
    { label: "下载量", value: "downloads" },
    { label: "评分", value: "rating" },
  ];

  // Filter and sort logic
  const filteredData = mockOperators.filter((item) => {
    // Search filter
    if (
      searchTerm &&
      !item.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !item.description.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }

    // Category filter
    if (
      selectedFilters.category?.length &&
      !selectedFilters.category.includes(item.category)
    ) {
      return false;
    }

    // Type filter
    if (
      selectedFilters.type?.length &&
      !selectedFilters.type.includes(item.type)
    ) {
      return false;
    }

    // Modality filter
    if (
      selectedFilters.modality?.length &&
      !selectedFilters.modality.includes(item.modality)
    ) {
      return false;
    }

    // Status filter
    if (
      selectedFilters.status?.length &&
      !selectedFilters.status.includes(item.status)
    ) {
      return false;
    }

    // Price filter
    if (
      selectedFilters.price?.length &&
      !selectedFilters.price.includes(item.price)
    ) {
      return false;
    }

    return true;
  });

  // Sort data
  if (sortBy) {
    filteredData.sort((a, b) => {
      let aValue: any = a[sortBy as keyof Operator];
      let bValue: any = b[sortBy as keyof Operator];

      if (typeof aValue === "string") {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }

  // 视图状态管理
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");
  const [favoriteOperators, setFavoriteOperators] = useState<Set<number>>(
    new Set([1, 3, 6])
  );

  const filteredOperators = operators
    .filter((operator) => {
      const matchesSearch =
        operator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        operator.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        operator.author.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCategory =
        selectedCategories.length === 0 ||
        selectedCategories.includes(operator.category);
      const matchesType =
        selectedTypes.length === 0 || selectedTypes.includes(operator.type);
      const matchesModality =
        selectedModalities.length === 0 ||
        operator.modality.some((mod) => selectedModalities.includes(mod));
      const matchesStatus =
        selectedStatuses.length === 0 ||
        selectedStatuses.includes(operator.status);
      const matchesTags =
        selectedTags.length === 0 ||
        operator.tags.some((tag) => selectedTags.includes(tag));

      return (
        matchesSearch &&
        matchesCategory &&
        matchesType &&
        matchesModality &&
        matchesStatus &&
        matchesTags
      );
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "createdAt":
          return (
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
        case "lastModified":
          return (
            new Date(b.lastModified).getTime() -
            new Date(a.lastModified).getTime()
          );
        case "downloads":
          return b.downloads - a.downloads;
        case "usage":
          return b.usage - a.usage;
        default:
          return 0;
      }
    });

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: {
        label: "活跃",
        color: "green",
        icon: <Zap className="w-3 h-3" />,
      },
      beta: {
        label: "测试版",
        color: "blue",
        icon: <Settings className="w-3 h-3" />,
      },
      deprecated: {
        label: "已弃用",
        color: "gray",
        icon: <X className="w-3 h-3" />,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    );
  };

  const getTypeIcon = (type: string) => {
    const iconMap = {
      preprocessing: Code,
      training: Brain,
      inference: Cpu,
      postprocessing: Package,
    };
    const IconComponent = iconMap[type as keyof typeof iconMap] || Code;
    return <IconComponent className="w-4 h-4" />;
  };

  const getTypeColor = (type: string) => {
    const colorMap = {
      preprocessing: "bg-blue-100",
      training: "bg-green-100",
      inference: "bg-purple-100",
      postprocessing: "bg-orange-100",
    };
    return colorMap[type as keyof typeof colorMap] || "bg-blue-100";
  };

  const handleViewOperator = (operator: Operator) => {
    navigate(`/data/operator-market/plugin-detail/${operator.id}`);
  };

  const handleUploadOperator = () => {
    navigate(`/data/operator-market/create`);
  };

  const handleUpdateOperator = (operator: Operator) => {
    navigate(`/data/operator-market/create/${operator.id}`);
  };

  const handleToggleFavorite = (operatorId: number) => {
    setFavoriteOperators((prev) => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(operatorId)) {
        newFavorites.delete(operatorId);
      } else {
        newFavorites.add(operatorId);
      }
      return newFavorites;
    });

    setOperators((prev) =>
      prev.map((operator) =>
        operator.id === operatorId
          ? { ...operator, isFavorited: !operator.isFavorited }
          : operator
      )
    );
  };

  const handleCreateNewTag = () => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      setAvailableTags([...availableTags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleEditTag = (oldTag: string, newTag: string) => {
    if (newTag.trim() && newTag !== oldTag) {
      setAvailableTags(
        availableTags.map((tag) => (tag === oldTag ? newTag.trim() : tag))
      );
      setOperators(
        operators.map((operator) => ({
          ...operator,
          tags: operator.tags.map((tag) =>
            tag === oldTag ? newTag.trim() : tag
          ),
        }))
      );
    }
    setEditingTag(null);
    setEditingTagValue("");
  };

  const handleDeleteTag = (tagToDelete: string) => {
    setAvailableTags(availableTags.filter((tag) => tag !== tagToDelete));
    setOperators(
      operators.map((operator) => ({
        ...operator,
        tags: operator.tags.filter((tag) => tag !== tagToDelete),
      }))
    );
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex justify-between mb-2">
        <h1 className="text-xl font-bold text-gray-900">算子市场</h1>
        <div className="flex items-center">
          <div className="flex gap-2">
            <TagManagement />
            <Button
              type="primary"
              onClick={handleUploadOperator}
              icon={<Plus className="w-4 h-4 mr-2" />}
            >
              上传算子
            </Button>
          </div>
        </div>
      </div>
      {/* Main Content */}
      <div className="flex h-full bg-white rounded-lg">
        <div
          className={`border-r border-gray-200 transition-all duration-300 ${
            showFilters
              ? "translate-x-0 w-56"
              : "-translate-x-full w-0 opacity-0"
          }`}
        >
          <Filters />
        </div>
        <div className="flex-1 bg-yellow flex flex-col px-4">
          <div className="flex w-full items-center gap-4 border-b border-gray-200 mb-4">
            <Button
              type="text"
              icon={<FilterOutlined />}
              onClick={() => setShowFilters(!showFilters)}
            />
            <div className="flex-1 my-4">
              <SearchControls
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                searchPlaceholder="搜索算子..."
                filters={filterOptions}
                selectedFilters={selectedFilters}
                onFiltersChange={setSelectedFilters}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSortChange={(field, order) => {
                  setSortBy(field);
                  setSortOrder(order);
                }}
                sortOptions={sortOptions}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                showViewToggle={true}
              />
            </div>
          </div>
          {/* Content */}
          {filteredOperators.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                没有找到匹配的算子
              </h3>
              <p className="text-gray-500">尝试调整筛选条件或搜索关键词</p>
            </div>
          ) : (
            <>
              {viewMode === "card" ? (
                <CardView
                  className="mx-4"
                  data={filteredOperators.map((operator) => ({
                    ...operator,
                    icon: getTypeIcon(operator.type),
                    iconColor: getTypeColor(operator.type),
                    status: getStatusBadge(operator.status),
                    statistics: [
                      {
                        label: "使用次数",
                        value: operator.usage.toLocaleString(),
                      },
                      { label: "框架", value: operator.framework },
                      { label: "大小", value: operator.size },
                      { label: "语言", value: operator.language },
                    ],
                  }))}
                  pageSize={8}
                  operations={[
                    {
                      key: "view",
                      label: "查看详情",
                      onClick: handleViewOperator,
                    },
                    {
                      key: "edit",
                      label: "更新算子",
                      onClick: handleUpdateOperator,
                    },
                    {
                      key: "delete",
                      label: "删除算子",
                      onClick: handleDeleteTag,
                    },
                  ]}
                  onView={handleViewOperator}
                  onFavorite={(item) => handleToggleFavorite(item.id)}
                  isFavorite={(item) => favoriteOperators.has(item.id)}
                />
              ) : (
                <ListView operators={filteredOperators} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
