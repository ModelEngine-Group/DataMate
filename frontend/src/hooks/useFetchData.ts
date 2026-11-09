// 首页数据获取
// 支持轮询功能，使用示例：
// const { fetchData, startPolling, stopPolling, isPolling } = useFetchData(
//   fetchFunction,
//   mapFunction,
//   5000, // 5秒轮询一次，默认30秒
//   true, // 是否自动开始轮询，默认 true
//   [fetchStatistics, fetchOtherData] // 额外的轮询函数数组
// );
//
// startPolling(); // 开始轮询
// stopPolling();  // 停止轮询
// 手动调用 fetchData() 时，如果正在轮询，会重新开始轮询计时
// 轮询时会同时执行主要的 fetchFunction 和所有额外的轮询函数
import { useState, useRef, useEffect, useCallback } from "react";
import Loading from "@/utils/loading";
import { App } from "antd";
import { useTranslation } from "react-i18next";

interface SearchFilters {
  type?: string[];
  status?: string[];
  tags?: string[];
  categories?: string[][];
  selectedStar?: boolean;
  builtIn?: string[];
  [key: string]: string[] | string[][] | boolean | undefined;
}

export default function useFetchData<T>(
  fetchFunc: (params?: any) => Promise<any>,
  mapDataFunc: (data: Partial<T>) => T = (data) => data as T,
  pollingInterval: number = 30000, // Default polling interval 30 seconds
  autoRefresh: boolean = false, // Whether to auto start polling, default false
  additionalPollingFuncs: (() => Promise<any>)[] = [], // Additional polling functions
  pageOffset: number = 1
) {
  const { message } = App.useApp();
  const { t } = useTranslation();

  // 轮询相关状态
  const [isPolling, setIsPolling] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  // 表格数据
  const [tableData, setTableData] = useState<T[]>([]);
  // 设置加载状态
  const [loading, setLoading] = useState(false);

  // 搜索参数
  const [searchParams, setSearchParams] = useState({
    keyword: "",
    filter: {
      type: [] as string[],
      status: [] as string[],
      tags: [] as string[],
      categories: [] as string[][],
      selectedStar: false,
    } as SearchFilters,
    current: 1,
    pageSize: 12,
  });

  // 使用 ref 存储 searchParams 的值
  const searchParamsRef = useRef(searchParams);
  searchParamsRef.current = searchParams;

  // 组件挂载状态 ref
  const isMountedRef = useRef(true);
  
  // Pagination configuration
  const [pagination, setPagination] = useState({
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ["12", "24", "48"],
    showTotal: (total: number) => `${t('hooks.fetchData.totalItems')}: ${total}`,
    onChange: (current: number, pageSize?: number) => {
      setSearchParams((prev) => ({
        ...prev,
        current,
        pageSize: pageSize || prev.pageSize,
      }));
    },
  });

  const handleFiltersChange = (searchFilters: { [key: string]: string[] }) => {
    setSearchParams({
      ...searchParams,
      current: 1,
      filter: { ...searchParams.filter, ...searchFilters },
    });
  };

  const handleKeywordChange = (keyword: string) => {
    setSearchParams({
      ...searchParams,
      current: 1,
      keyword: keyword,
    });
  };

  function getFirstOfArray(arr?: string[]) {
    if (!arr || arr.length === 0 || !Array.isArray(arr)) return undefined;
    if (arr[0] === "all") return undefined;
    return arr[0];
  }

  // 清除轮询定时器
  const clearPollingTimer = useCallback(() => {
    if (pollingTimerRef.current) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  const fetchData = useCallback(
    async (extraParams = {}, skipPollingRestart = false) => {
      const { keyword, filter, current, pageSize } = searchParamsRef.current;
      
      if (!skipPollingRestart) {
        Loading.show();
        setLoading(true);
      }

      const wasPolling = isPollingRef.current && !skipPollingRestart;
      if (wasPolling) {
        clearPollingTimer();
      }

      try {
        const builtIn = getFirstOfArray(filter.builtIn);
        const apiParams: Record<string, unknown> = {
          categories: filter.categories,
          ...extraParams,
          keyword,
          isStar: filter.selectedStar ? true : undefined,
          type: getFirstOfArray(filter?.type) || undefined,
          status: getFirstOfArray(filter?.status) || undefined,
          built_in: builtIn === undefined ? undefined : builtIn === "true",
          tags: filter?.tags?.length ? filter.tags.join(",") : undefined,
          page: current - pageOffset,
          size: pageSize,
        };

        Object.entries(filter).forEach(([key, value]) => {
          if (!["type", "status", "tags", "categories", "selectedStar", "builtIn"].includes(key)) {
            apiParams[key] = Array.isArray(value) ? getFirstOfArray(value as string[]) : value;
          }
        });

        Object.keys(searchParamsRef.current).forEach(key => {
          if (!['keyword', 'filter', 'current', 'pageSize'].includes(key) && apiParams[key as keyof typeof apiParams] === undefined) {
            (apiParams as any)[key] = (searchParamsRef.current as any)[key];
          }
        });

        const promises = [
          fetchFunc(apiParams),
          ...additionalPollingFuncs.map((func) => func()),
        ];

        const results = await Promise.all(promises);
        const { data } = results[0];

        if (!isMountedRef.current) {
          return;
        }

        setPagination((prev) => ({
          ...prev,
          total: data?.totalElements || 0,
        }));
        let result = [];
        if (mapDataFunc) {
          result = data?.content?.map(mapDataFunc) ?? [];
        }
        setTableData(result);
      } catch (error) {
        if (!isMountedRef.current) {
          return;
        }

        if (error && typeof error === "object" && "status" in error && error.status === 401) {
          message.warning(t('hooks.fetchData.loginRequired'));
        } else {
          message.error(t('hooks.fetchData.fetchFailed'));
        }
      } finally {
        if (isMountedRef.current && !skipPollingRestart) {
          Loading.hide();
          setLoading(false);
        }
        if (wasPolling && isPollingRef.current && isMountedRef.current) {
          const poll = () => {
            pollingTimerRef.current = setTimeout(() => {
              fetchDataRef.current({}, true).then(() => {
                if (isPollingRef.current && isMountedRef.current) {
                  poll();
                }
              });
            }, pollingInterval);
          };
          poll();
        }
      }
    },
    [
      fetchFunc,
      mapDataFunc,
      clearPollingTimer,
      pollingInterval,
      message,
      t,
      pageOffset,
      additionalPollingFuncs,
    ]
  );

  // 开始轮询
  const startPolling = useCallback(() => {
    clearPollingTimer();
    setIsPolling(true);
    isPollingRef.current = true;

    const poll = () => {
      pollingTimerRef.current = setTimeout(() => {
        fetchDataRef.current({}, true).then(() => {
          if (isPollingRef.current && isMountedRef.current) {
            poll();
          }
        });
      }, pollingInterval);
    };

    poll();
  }, [pollingInterval, clearPollingTimer, fetchData]);

  // 停止轮询
  const stopPolling = useCallback(() => {
    clearPollingTimer();
    setIsPolling(false);
    isPollingRef.current = false;
  }, [clearPollingTimer]);

  // 使用最新回调，避免内联映射函数变化取消尚未执行的搜索请求。
  const fetchDataRef = useRef(fetchData);
  fetchDataRef.current = fetchData;
  const searchParamsKey = JSON.stringify(searchParams);

  useEffect(() => {
    // 防抖处理
    const timer = setTimeout(() => {
      if (isMountedRef.current) {
        fetchDataRef.current();
      }
    }, searchParamsRef.current.keyword ? 500 : 0);
    
    return () => {
      clearTimeout(timer);
    };
  }, [searchParamsKey]);

  // 组件卸载时清理轮询和状态
  useEffect(() => {
    isMountedRef.current = true;
    
    if (autoRefresh) {
      startPolling();
    }
    
    return () => {
      isMountedRef.current = false;
      clearPollingTimer();
      Loading.hideAll();
    };
  }, []);

  return {
    loading,
    tableData,
    pagination: {
      ...pagination,
      current: searchParams.current,
      pageSize: searchParams.pageSize,
    },
    searchParams,
    setSearchParams,
    setPagination,
    handleFiltersChange,
    handleKeywordChange,
    fetchData,
    isPolling,
    startPolling,
    stopPolling,
  };
}
