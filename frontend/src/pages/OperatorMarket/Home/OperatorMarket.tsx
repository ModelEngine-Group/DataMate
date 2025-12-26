import { useEffect, useState } from "react";
import { Button, message } from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  FilterOutlined,
  PlusOutlined,
  DownloadOutlined
} from "@ant-design/icons";
import { Boxes } from "lucide-react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import type {
  CategoryTreeI,
  OperatorI,
} from "@/pages/OperatorMarket/operator.model";
import Filters from "./components/Filters";
import TagManagement from "@/components/business/TagManagement";
import { ListView } from "./components/List";
import useFetchData from "@/hooks/useFetchData";
import {
  deleteOperatorByIdUsingDelete,
  downloadExampleOperatorUsingGet,
  queryCategoryTreeUsingGet,
  queryOperatorsUsingPost,
} from "../operator.api";
import { mapOperator } from "../operator.const";

export default function OperatorMarketPage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});

  const [showFilters, setShowFilters] = useState(true);
  const [categoriesTree, setCategoriesTree] = useState<CategoryTreeI[]>([]);

  const initCategoriesTree = async () => {
    const { data } = await queryCategoryTreeUsingGet({ page: 0, size: 1000 });
    setCategoriesTree(data.content || []);
  };

  useEffect(() => {
    initCategoriesTree();
  }, []);

  const {
    tableData,
    pagination,
    searchParams,
    fetchData,
    handleFiltersChange,
    handleKeywordChange,
  } = useFetchData(queryOperatorsUsingPost, mapOperator);

  const handleUploadOperator = () => {
    navigate(`/data/operator-market/create`);
  };

  const handleDownload = async () => {
    await downloadExampleOperatorUsingGet("test_operator.tar");
    message.success("文件下载成功");
  };

  const handleUpdateOperator = (operator: OperatorI) => {
    navigate(`/data/operator-market/create/${operator.id}`);
  };

  const handleDeleteOperator = async (operator: OperatorI) => {
    try {
      await deleteOperatorByIdUsingDelete(operator.id);
      message.success("算子删除成功");
      fetchData();
    } catch (error) {
      message.error("算子删除失败");
    }
  };

  const operations = [
    {
      key: "edit",
      label: "更新",
      icon: <EditOutlined />,
      onClick: handleUpdateOperator,
    },
    {
      key: "delete",
      label: "删除",
      danger: true,
      icon: <DeleteOutlined />,
      confirm: {
        title: "确认删除",
        description: "此操作不可撤销，是否继续？",
        okText: "删除",
        okType: "danger",
        cancelText: "取消",
      },
      onClick: handleDeleteOperator,
    },
  ];

  useEffect(() => {
    if (Object.keys(selectedFilters).length === 0) {
      return;
    }
    const filteredIds = Object.values(selectedFilters).reduce(
      (acc, filter: string[]) => {
        if (filter.length) {
          acc.push(...filter);
        }

        return acc;
      },
      []
    );
    
    fetchData({ categories: filteredIds?.length ? filteredIds : undefined });
  }, [selectedFilters]);

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex justify-between">
        <h1 className="text-xl font-bold text-gray-900">算子市场</h1>
        <div className="flex gap-2">
          {/*<TagManagement />*/}
          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownload}
          >
            下载示例算子
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleUploadOperator}
          >
            上传算子
          </Button>
        </div>
      </div>
      {/* Main Content */}
      <div className="flex-overflow-auto flex-row border-card">
        <div
          className={`border-r border-gray-100 transition-all duration-300 ${
            showFilters
              ? "translate-x-0 w-56"
              : "-translate-x-full w-0 opacity-0"
          }`}
        >
          <Filters
            hideFilter={() => setShowFilters(false)}
            categoriesTree={categoriesTree}
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
          />
        </div>
        <div className="flex-overflow-auto p-6 ">
          <div className="flex w-full items-top gap-4 border-b border-gray-200 mb-4">
            {!showFilters && (
              <Button
                type="text"
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(true)}
              />
            )}
            <div className="flex-1 mb-4">
              <SearchControls
                searchTerm={searchParams.keyword}
                onSearchChange={handleKeywordChange}
                searchPlaceholder="搜索算子名称、描述..."
                filters={[]}
                onFiltersChange={handleFiltersChange}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                showViewToggle={true}
                onReload={fetchData}
              />
            </div>
          </div>
          {/* Content */}
          {tableData.length === 0 ? (
            <div className="text-center py-12">
              <Boxes className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                没有找到匹配的算子
              </h3>
              <p className="text-gray-500">尝试调整筛选条件或搜索关键词</p>
            </div>
          ) : (
            <>
              {viewMode === "card" ? (
                <CardView
                  data={tableData}
                  pagination={pagination}
                  operations={operations}
                  onView={(item) => navigate(`/data/operator-market/plugin-detail/${item.id}`)}
                />
              ) : (
                <ListView
                  operators={tableData}
                  operations={operations}
                  pagination={pagination}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
