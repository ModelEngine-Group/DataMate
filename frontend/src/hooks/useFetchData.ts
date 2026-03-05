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
import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useDebouncedEffect } from "./useDebouncedEffect";
import Loading from "@/utils/loading";
import { App } from "antd";
import { useTranslation } from "react-i18next";

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
    },
    current: 1,
    pageSize: 12,
  });

  // 使用 ref 存储 searchParams 的值
  const searchParamsRef = useRef(searchParams);
  searchParamsRef.current = searchParams;

  // 组件挂载状态 ref
  const isMountedRef = useRef(true);
  
  // 跟踪上一次的 searchParams，用于避免重复请求
  const prevSearchParamsRef = useRef<string>("");

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

  function getFirstOfArray(arr: string[]) {
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
        const apiParams = {
          categories: filter.categories,
          ...extraParams,
          keyword,
          isStar: filter.selectedStar ? true : undefined,
          type: getFirstOfArray(filter?.type) || undefined,
          status: getFirstOfArray(filter?.status) || undefined,
          built_in: filter?.builtIn !== undefined ? (getFirstOfArray(filter?.builtIn) === "true") : undefined,
          tags: filter?.tags?.length ? filter.tags.join(",") : undefined,
          page: current - pageOffset,
          size: pageSize,
        };

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
          result = data?.content.map(mapDataFunc) ?? [];
        }
        setTableData(result);

        if (wasPolling) {
          const poll = () => {
            pollingTimerRef.current = setTimeout(() => {
              fetchData({}, true).then(() => {
                if (pollingTimerRef.current && isMountedRef.current) {
                  poll();
                }
              });
            }, pollingInterval);
          };
          poll();
        }
      } catch (error) {
        if (!isMountedRef.current) {
          return;
        }
        
        if (error.status === 401) {
          message.warn(t('hooks.fetchData.loginRequired'));
        } else {
          message.error(t('hooks.fetchData.fetchFailed'));
        }
      } finally {
        if (isMountedRef.current) {
          Loading.hide();
          setLoading(false);
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
        fetchData({}, true).then(() => {
          if (pollingTimerRef.current && isMountedRef.current) {
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

  // 搜索参数变化时，自动刷新数据
  // 使用 useEffect + 深比较，而不是将对象作为依赖项
  useEffect(() => {
    if (!isMountedRef.current) return;
    
    // 序列化当前参数
    const currentParamsString = JSON.stringify({
      keyword: searchParams.keyword,
      filterType: searchParams.filter.type,
      filterStatus: searchParams.filter.status,
      filterTags: searchParams.filter.tags,
      filterCategories: searchParams.filter.categories,
      selectedStar: searchParams.filter.selectedStar,
      current: searchParams.current,
      pageSize: searchParams.pageSize,
    });
    
    // 检查参数是否真的变化了
    if (currentParamsString === prevSearchParamsRef.current) {
      return;
    }
    prevSearchParamsRef.current = currentParamsString;
    
    // 防抖处理
    const timer = setTimeout(() => {
      if (isMountedRef.current) {
        fetchData();
      }
    }, searchParams?.keyword ? 500 : 0);
    
    return () => {
      clearTimeout(timer);
    };
  }, [searchParams, fetchData]);

  // 组件挂载时重置 prevSearchParamsRef，解决 StrictMode 双重挂载问题
  useEffect(() => {
    prevSearchParamsRef.current = "";
  }, []);

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
