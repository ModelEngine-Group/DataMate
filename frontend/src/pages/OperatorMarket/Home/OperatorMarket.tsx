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
import { useTranslation } from "react-i18next";
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
  queryOperatorsUsingPost, updateOperatorByIdUsingPut,
} from "../operator.api";
import { mapOperator } from "../operator.const";

export default function OperatorMarketPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});

  const [showFilters, setShowFilters] = useState(true);
  const [categoriesTree, setCategoriesTree] = useState<CategoryTreeI[]>([]);
  const [starCount, setStarCount] = useState(0);
  const [selectedStar, setSelectedStar] = useState<boolean>(false);

  const initCategoriesTree = async () => {
    const { data } = await queryCategoryTreeUsingGet({ page: 0, size: 1000 });
    setCategoriesTree(data.content || []);
    setStarCount(data.starCount || 0);
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
    handleKeywordChange,
  } = useFetchData(queryOperatorsUsingPost, (op) => mapOperator(op, t));

  const handleUploadOperator = () => {
    navigate(`/data/operator-market/create`);
  };

  const handleDownload = async () => {
    await downloadExampleOperatorUsingGet("test_operator.tar");
    message.success(t("operatorMarket.home.operations.messages.downloadSuccess"));
  };

  const handleUpdateOperator = (operator: OperatorI) => {
    navigate(`/data/operator-market/create/${operator.id}`);
  };

  const handleDeleteOperator = async (operator: OperatorI) => {
    await deleteOperatorByIdUsingDelete(operator.id);
    message.success(t("operatorMarket.home.operations.messages.deleteSuccess"));
    fetchData();
    await initCategoriesTree();
  };

  const handleStar = async (operator: OperatorI) => {
    const data = {
      id: operator.id,
      isStar: !operator.isStar
    };
    await updateOperatorByIdUsingPut(operator.id, data);
    fetchData();
    await initCategoriesTree();
  }

  const operations = [
    {
      key: "edit",
      label: t("operatorMarket.home.operations.update"),
      icon: <EditOutlined />,
      onClick: handleUpdateOperator,
    },
    {
      key: "delete",
      label: t("operatorMarket.home.operations.delete"),
      danger: true,
      icon: <DeleteOutlined />,
      confirm: {
        title: t("operatorMarket.home.operations.confirm.title"),
        description: t("operatorMarket.home.operations.confirm.description"),
        okText: t("operatorMarket.home.operations.confirm.okText"),
        okType: "danger",
        cancelText: t("operatorMarket.home.operations.confirm.cancelText"),
      },
      onClick: handleDeleteOperator,
    },
  ];

  useEffect(() => {
    const filteredIds = Object.values(selectedFilters).filter(item => item.length > 0);

    // 分类筛选变化时：
    // 1. 将分类 ID 写入通用 searchParams.filter.categories，确保分页时条件不会丢失
    // 2. 将页码重置为 1，避免从“全选”页的当前页跳入细分列表的同一页
    setSearchParams((prev) => ({
      ...prev,
      current: 1,
      filter: {
        ...prev.filter,
        categories: filteredIds,
        selectedStar: selectedStar,
      },
    }));
  }, [selectedFilters, setSearchParams, selectedStar]);

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex justify-between">
        <h1 className="text-xl font-bold text-gray-900">{t("operatorMarket.title")}</h1>
        <div className="flex gap-2">
          {/*<TagManagement />*/}
          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownload}
          >
            {t("operatorMarket.home.actions.downloadExample")}
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleUploadOperator}
          >
            {t("operatorMarket.home.actions.upload")}
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
            selectedStar={selectedStar}
            starCount={starCount}
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
            setSelectedStar={setSelectedStar}
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
                searchPlaceholder={t("operatorMarket.home.search.placeholder")}
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
                {t("operatorMarket.home.empty.title")}
              </h3>
              <p className="text-gray-500">{t("operatorMarket.home.empty.subtitle")}</p>
            </div>
          ) : (
            <>
              {viewMode === "card" ? (
                <CardView
                  data={tableData}
                  pagination={pagination}
                  operations={operations}
                  onFavorite={handleStar}
                  isFavorite={(operator: OperatorI) => operator.isStar}
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
