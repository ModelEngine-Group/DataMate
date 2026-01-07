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
import { useDebouncedEffect } from "./useDebouncedEffect";
import Loading from "@/utils/loading";
import { App } from "antd";

export default function useFetchData<T>(
  fetchFunc: (params?: any) => Promise<any>,
  mapDataFunc: (data: Partial<T>) => T = (data) => data as T,
  pollingInterval: number = 30000, // 默认30秒轮询一次
  autoRefresh: boolean = false, // 是否自动开始轮询，默认 false
  additionalPollingFuncs: (() => Promise<any>)[] = [], // 额外的轮询函数
  pageOffset: number = 1
) {
  const { message } = App.useApp();

  // 轮询相关状态
  const [isPolling, setIsPolling] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

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
      // 通用分类筛选（如算子市场的分类 ID 列表）
      categories: [] as string[][],
      selectedStar: false,
    },
    current: 1,
    pageSize: 12,
  });

  // 分页配置
  const [pagination, setPagination] = useState({
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ["12", "24", "48"],
    showTotal: (total: number) => `共 ${total} 条`,
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
      const { keyword, filter, current, pageSize } = searchParams;
      if (!skipPollingRestart) {
        Loading.show();
        setLoading(true);
      }

      // 如果正在轮询且不是轮询触发的调用，先停止当前轮询
      const wasPolling = isPolling && !skipPollingRestart;
      if (wasPolling) {
        clearPollingTimer();
      }

      try {
        // 同时执行主要数据获取和额外的轮询函数
        const promises = [
          fetchFunc({
            categories: filter.categories,
            ...extraParams,
            keyword,
            isStar: filter.selectedStar ? true : undefined,
            type: getFirstOfArray(filter?.type) || undefined,
            status: getFirstOfArray(filter?.status) || undefined,
            tags: filter?.tags?.length ? filter.tags.join(",") : undefined,
            page: current - pageOffset,
            size: pageSize,  // Use camelCase for HTTP query params
          }),
          ...additionalPollingFuncs.map((func) => func()),
        ];

        const results = await Promise.all(promises);
        const { data } = results[0]; // 主要数据结果

        setPagination((prev) => ({
          ...prev,
          total: data?.totalElements || 0,
        }));
        let result = [];
        if (mapDataFunc) {
          result = data?.content.map(mapDataFunc) ?? [];
        }
        setTableData(result);

        // 如果之前正在轮询且不是轮询触发的调用，重新开始轮询
        if (wasPolling) {
          const poll = () => {
            pollingTimerRef.current = setTimeout(() => {
              fetchData({}, true).then(() => {
                if (pollingTimerRef.current) {
                  poll();
                }
              });
            }, pollingInterval);
          };
          poll();
        }
      } catch (error) {
        console.error(error);
        message.error("数据获取失败，请稍后重试");
      } finally {
        Loading.hide();
        setLoading(false);
      }
    },
    [
      searchParams,
      fetchFunc,
      mapDataFunc,
      isPolling,
      clearPollingTimer,
      pollingInterval,
      message,
      additionalPollingFuncs,
    ]
  );

  // 开始轮询
  const startPolling = useCallback(() => {
    clearPollingTimer();
    setIsPolling(true);

    const poll = () => {
      pollingTimerRef.current = setTimeout(() => {
        fetchData({}, true).then(() => {
          if (pollingTimerRef.current) {
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
  }, [clearPollingTimer]);

  // 搜索参数变化时，自动刷新数据
  // keyword 变化时，防抖500ms后刷新
  useDebouncedEffect(
    () => {
      fetchData();
    },
    [searchParams],
    searchParams?.keyword ? 500 : 0
  );

  // 组件卸载时清理轮询
  useEffect(() => {
    if (autoRefresh) {
      startPolling();
    }
    return () => {
      clearPollingTimer();
    };
  }, [clearPollingTimer]);

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
