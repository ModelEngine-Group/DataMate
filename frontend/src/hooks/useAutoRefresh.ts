import { useState, useEffect, useRef, useCallback } from 'react';

interface UsePreciseAutoRefreshOptions<T> {
  fetchData: () => Promise<T>;
  interval?: number;
  enabled?: boolean;
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useAutoRefresh<T>({
                                           fetchData,
                                           interval = 5000,
                                           enabled = true,
                                           immediate = true,
                                           onSuccess,
                                           onError
                                         }: UsePreciseAutoRefreshOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const timeoutRef = useRef<NodeJS.Timeout>();
  const isMounted = useRef(true);
  const enabledRef = useRef(enabled);
  const intervalRef = useRef(interval);

  // 更新 ref 值
  useEffect(() => {
    enabledRef.current = enabled;
    intervalRef.current = interval;
  }, [enabled, interval]);

  const executeFetch = useCallback(async () => {
    if (!isMounted.current || !enabledRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchData();
      if (isMounted.current) {
        setData(result);
        onSuccess?.(result);
      }
    } catch (err) {
      if (isMounted.current) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        onError?.(error);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);

        // 无论成功失败，都安排下一次轮询
        if (enabledRef.current) {
          timeoutRef.current = setTimeout(executeFetch, intervalRef.current);
        }
      }
    }
  }, [fetchData, onSuccess, onError]);

  const startPolling = useCallback(() => {
    if (!enabledRef.current) return;

    // 清理现有的定时器
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // 开始轮询
    timeoutRef.current = setTimeout(executeFetch, intervalRef.current);
  }, [executeFetch]);

  const stopPolling = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = undefined;
    }
  }, []);

  const refresh = useCallback(async () => {
    if (!isMounted.current) return;

    // 手动刷新时，先停止当前的轮询
    stopPolling();

    setLoading(true);
    setError(null);

    try {
      const result = await fetchData();
      if (isMounted.current) {
        setData(result);
        onSuccess?.(result);
      }
    } catch (err) {
      if (isMounted.current) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        onError?.(error);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
        // 手动刷新后重新开始轮询
        if (enabledRef.current) {
          startPolling();
        }
      }
    }
  }, [fetchData, onSuccess, onError, stopPolling, startPolling]);

  useEffect(() => {
    isMounted.current = true;
    enabledRef.current = enabled;

    if (enabled) {
      if (immediate) {
        // 立即执行第一次
        executeFetch();
      } else {
        // 延迟第一次执行
        startPolling();
      }
    } else {
      stopPolling();
    }

    return () => {
      isMounted.current = false;
      stopPolling();
    };
  }, [enabled, immediate, executeFetch, startPolling, stopPolling]);

  // 当 interval 变化时重新调整轮询
  useEffect(() => {
    if (enabled) {
      stopPolling();
      startPolling();
    }
  }, [interval, enabled, stopPolling, startPolling]);

  return {
    data,
    loading,
    error,
    refresh,
    startPolling,
    stopPolling,
    isPolling: !!timeoutRef.current
  };
}