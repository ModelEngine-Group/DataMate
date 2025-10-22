import { useEffect, useState } from "react";
import { Button } from "antd";
import { FilterOutlined, PlusOutlined } from "@ant-design/icons";
import { Boxes } from "lucide-react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import type {
  CategoryTreeI,
  OperatorI,
} from "@/pages/OperatorMarket/operator.model";
import Filters from "./components/Filters";
import TagManagement from "@/components/TagManagement";
import { ListView } from "./components/List";
import useFetchData from "@/hooks/useFetchData";
import {
  queryCategoryTreeUsingGet,
  queryOperatorsUsingPost,
} from "../operator.api";
import { mapOperator } from "../operator.const";

export default function OperatorMarketPage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const filterOptions = [];

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
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryOperatorsUsingPost, mapOperator);

  const handleViewOperator = (operator: OperatorI) => {
    navigate(`/data/operator-market/plugin-detail/${operator.id}`);
  };

  const handleUploadOperator = () => {
    navigate(`/data/operator-market/create`);
  };

  const handleUpdateOperator = (operator: OperatorI) => {
    navigate(`/data/operator-market/edit/${operator.id}`);
  };

  const handleDeleteTag = (operator: OperatorI) => {
    // 删除算子逻辑
    console.log("删除算子", operator);
  };

  const operations = [
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
  ];

  useEffect(() => {
    if (Object.keys(selectedFilters).length === 0) {
      return;
    }
    const filteredIds = Object.values(selectedFilters).reduce(
      (acc, filter: string[]) => {
        if (filter.length) {
          acc.push(...filter.map(Number));
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
        {/* <div className="flex gap-2">
          <TagManagement />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleUploadOperator}
          >
            上传算子
          </Button>
        </div> */}
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
                onSearchChange={(keyword) =>
                  setSearchParams({ ...searchParams, keyword })
                }
                searchPlaceholder="搜索算子名称、描述..."
                filters={filterOptions}
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
                <CardView data={tableData} pagination={pagination} />
              ) : (
                <ListView operators={tableData} pagination={pagination} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
