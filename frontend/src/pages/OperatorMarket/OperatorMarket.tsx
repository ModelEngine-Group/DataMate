import { useState } from "react";
import { Button, Input, Badge, Drawer, List, Avatar, Tag } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import {
  Plus,
  Eye,
  Edit,
  Star,
  TagIcon,
  Save,
  Trash2,
  X,
  Code,
  Cpu,
  ImageIcon,
  FileText,
  Music,
  Video,
  Brain,
  Zap,
  Settings,
  Package,
} from "lucide-react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import { mockOperators } from "@/mock/operator";
import type { Operator } from "@/types/operator";
import { mockTags } from "@/mock/dataset";
import Filters from "./components/Filters";

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
  const [availableTags, setAvailableTags] = useState<string[]>(mockTags);
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

  const getModalityIcon = (modality: string) => {
    const iconMap = {
      text: FileText,
      image: ImageIcon,
      audio: Music,
      video: Video,
    };
    const IconComponent = iconMap[modality as keyof typeof iconMap] || FileText;
    return <IconComponent className="w-3 h-3" />;
  };

  const handleViewOperator = (operator: Operator) => {
    navigate(`/data/operator-market/plugin-detail/${operator.id}`);
  };

  const handleUploadOperator = () => {
    navigate(`/data/operator-market/upload-operator`);
  };

  const handleUpdateOperator = (operator: Operator) => {
    navigate(`/data/operator-market/${operator.id}/edit`);
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

  const renderCardView = (
    <CardView className="mx-4"
      data={filteredOperators.map((operator) => ({
        ...operator,
        icon: getTypeIcon(operator.type),
        iconColor: getTypeColor(operator.type),
        status: getStatusBadge(operator.status),
        statistics: [
          { label: "使用次数", value: operator.usage.toLocaleString() },
          { label: "框架", value: operator.framework },
          { label: "大小", value: operator.size },
          { label: "语言", value: operator.language },
        ],
      }))}
      pageSize={8}
      operations={[
        { key: "view", label: "查看详情", onClick: handleViewOperator },
        { key: "edit", label: "更新算子", onClick: handleUpdateOperator },
        { key: "delete", label: "删除算子", onClick: handleDeleteTag },
      ]}
      onView={handleViewOperator}
      onFavorite={(item) => handleToggleFavorite(item.id)}
      isFavorite={(item) => favoriteOperators.has(item.id)}
    />
  );

  const renderListView = (
    <List
      className="rounded-lg border border-gray-200 p-4 overflow-auto mx-4"
      dataSource={filteredOperators}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) =>
          `${range[0]}-${range[1]} 共 ${total} 个算子`,
      }}
      renderItem={(operator) => (
        <List.Item
          className="hover:bg-gray-50 transition-colors px-6 py-4"
          actions={[
            <Button
              key="view"
              type="text"
              size="small"
              onClick={() => handleViewOperator(operator)}
              icon={<Eye className="w-4 h-4" />}
              title="查看详情"
            />,
            <Button
              key="edit"
              type="text"
              size="small"
              onClick={() => handleUpdateOperator(operator)}
              icon={<Edit className="w-4 h-4" />}
              title="更新算子"
            />,
            <Button
              key="favorite"
              type="text"
              size="small"
              onClick={() => handleToggleFavorite(operator.id)}
              className={
                favoriteOperators.has(operator.id)
                  ? "text-yellow-500 hover:text-yellow-600"
                  : "text-gray-400 hover:text-yellow-500"
              }
              icon={
                <Star
                  className={`w-4 h-4 ${
                    favoriteOperators.has(operator.id) ? "fill-current" : ""
                  }`}
                />
              }
              title="收藏"
            />,
            <Button
              key="delete"
              type="text"
              size="small"
              danger
              icon={<Trash2 className="w-4 h-4" />}
              title="删除算子"
            />,
          ]}
        >
          <List.Item.Meta
            avatar={
              <Avatar
                className={`${getTypeColor(
                  operator.type
                )} flex items-center justify-center`}
                icon={getTypeIcon(operator.type)}
                size="large"
              />
            }
            title={
              <div className="flex items-center gap-3">
                <span
                  className="font-medium text-gray-900 cursor-pointer hover:text-blue-600"
                  onClick={() => handleViewOperator(operator)}
                >
                  {operator.name}
                </span>
                <Tag color="default">v{operator.version}</Tag>
                <Badge color={getStatusBadge(operator.status).color}>
                  {getStatusBadge(operator.status).label}
                </Badge>
              </div>
            }
            description={
              <div className="space-y-2">
                <div className="text-gray-600 ">
                  {operator.description}
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>作者: {operator.author}</span>
                  <span>类型: {operator.type}</span>
                  <span>框架: {operator.framework}</span>
                  <span>使用次数: {operator.usage.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">模态:</span>
                  {operator.modality.map((mod, index) => (
                    <Tag
                      key={index}
                      size="small"
                      icon={getModalityIcon(mod)}
                      className="flex items-center gap-1"
                    >
                      {mod}
                    </Tag>
                  ))}
                </div>
              </div>
            }
          />
        </List.Item>
      )}
    />
  );

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex justify-between mb-2">
        <h1 className="text-xl font-bold text-gray-900">算子市场</h1>
        <div className="flex items-center">
          <div className="flex gap-2">
            <Button
              onClick={() => setShowTagManager(true)}
              icon={<TagIcon className="w-4 h-4 mr-2" />}
            >
              标签管理
            </Button>
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
            showFilters ? "translate-x-0 w-56" : "-translate-x-full w-0 opacity-0"
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
            <div className="flex-1">
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
            <>{viewMode === "card" ? renderCardView : renderListView}</>
          )}
        </div>
      </div>

      {/* Tag Manager */}
      <Drawer
        visible={showTagManager}
        onClose={() => setShowTagManager(false)}
        title="标签管理"
      >
        <div className=" mt-6">
          {/* Add New Tag */}
          <div className="space-y-2">
            <label>添加新标签</label>
            <div className="flex gap-2">
              <Input
                placeholder="输入标签名称..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    handleCreateNewTag();
                  }
                }}
              />
              <Button onClick={handleCreateNewTag} disabled={!newTag.trim()}>
                <Plus className="w-4 h-4 mr-2" />
                添加
              </Button>
            </div>
          </div>

          {/* Existing Tags */}
          <div className="grid grid-cols-2 gap-2">
            {availableTags.map((tag) => (
              <div
                key={tag}
                className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50"
              >
                {editingTag === tag ? (
                  <div className="flex gap-2 flex-1">
                    <Input
                      value={editingTagValue}
                      onChange={(e) => setEditingTagValue(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          handleEditTag(tag, editingTagValue);
                        }
                        if (e.key === "Escape") {
                          setEditingTag(null);
                          setEditingTagValue("");
                        }
                      }}
                      className="h-6 "
                      autoFocus
                    />
                    <Button
                      onClick={() => handleEditTag(tag, editingTagValue)}
                      className="h-6 w-6 p-0"
                    >
                      <Save className="w-3 h-3" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <span className="">{tag}</span>
                    <div className="flex gap-1">
                      <Button
                        onClick={() => {
                          setEditingTag(tag);
                          setEditingTagValue(tag);
                        }}
                        className="h-6 w-6 p-0"
                      >
                        <Edit className="w-3 h-3" />
                      </Button>
                      <Button
                        onClick={() => handleDeleteTag(tag)}
                        className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </Drawer>
    </div>
  );
}
