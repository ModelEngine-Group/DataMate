import { useEffect, useState, useRef, useMemo } from "react";
import { useParams } from "react-router";
import { FileClock, Download } from "lucide-react";
import { useTranslation } from "react-i18next";
import { App } from "antd";
import VirtualList from 'rc-virtual-list';
import { streamCleaningTaskLog, downloadCleaningTaskLog } from "../../cleansing.api";
import { TaskStatus } from "../../cleansing.model";

interface LogEntry {
  level: string;
  message: string;
}

interface LogEntryWithIndex extends LogEntry {
  index: number;
}

export default function LogsTable({
  taskLog: initialLogs,
  fetchTaskLog,
  retryCount,
  taskName,
  taskStatus
}: {
  taskLog: LogEntry[],
  fetchTaskLog: () => Promise<LogEntry[]>,
  retryCount: number,
  taskName: string,
  taskStatus?: TaskStatus
}) {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const [selectedLog, setSelectedLog] = useState(retryCount + 1);
  const [streamingLogs, setStreamingLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const { message } = App.useApp();

  // Only stream when task is RUNNING and viewing the latest run
  const shouldStream = taskStatus === TaskStatus.RUNNING && selectedLog - 1 === retryCount;

  useEffect(() => {
    if (shouldStream) {
      startStreaming();
    } else {
      stopStreaming();
      fetchTaskLog(selectedLog - 1).then(() => {
        // Static logs loaded, safe to clear streaming logs now
        setStreamingLogs([]);
      });
    }
    return () => stopStreaming();
  }, [id, selectedLog, retryCount, shouldStream]);

  const startStreaming = () => {
    stopStreaming();
    setStreamingLogs([]);
    setIsStreaming(true);

    const eventSource = streamCleaningTaskLog(id, selectedLog - 1);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const logEntry: LogEntry = JSON.parse(event.data);
        if (logEntry.message === "[END_OF_STREAM]" || logEntry.message === "[HEARTBEAT]") {
          if (logEntry.message === "[END_OF_STREAM]") {
            // Don't clear streamingLogs immediately - keep them visible
            // while the static fetch completes
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            setIsStreaming(false);
          }
          return;
        }
        setStreamingLogs(prev => [...prev, logEntry]);
      } catch (e) {
        console.error("Failed to parse log entry:", e);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      stopStreaming();
    };
  };

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  // Use streaming logs only when actively streaming, otherwise use initial logs
  // Keep streamingLogs visible until initialLogs are populated (avoids blank flash)
  const displayLogs = isStreaming || streamingLogs.length > 0
    ? (streamingLogs.length > 0 ? streamingLogs : initialLogs)
    : initialLogs;

  // Add index to logs for virtual list key
  const logsWithIndex: LogEntryWithIndex[] = useMemo(() => {
    return (displayLogs || []).map((log, index) => ({ ...log, index }));
  }, [displayLogs]);

  // Get log level color class
  const getLevelClass = (level: string) => {
    if (level === "ERROR" || level === "FATAL") return "text-red-500";
    if (level === "WARNING" || level === "WARN") return "text-yellow-500";
    return "text-green-500";
  };

  const handleSelectChange = (value: number) => {
    setSelectedLog(value);
    setStreamingLogs([]);
  };

  const handleDownload = async () => {
    try {
      const blob = await downloadCleaningTaskLog(id, selectedLog - 1);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${taskName}_${t("dataCleansing.logTable.nthRun", { num: selectedLog })}.log`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to download log:", error);
      message.error(t("dataCleansing.detail.logTable.downloadFailed"));
    }
  };

  return displayLogs?.length > 0 || isStreaming ? (
    <>
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-500">{t("dataCleansing.detail.logTable.selectRun")}:</label>
          <select
            value={selectedLog}
            onChange={(e) => handleSelectChange(Number(e.target.value))}
            className="bg-gray-700 border border-gray-600 !text-white text-sm rounded-md focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1.5 min-w-[120px]"
          >
            {Array.from({ length: retryCount + 1 }, (_, i) => retryCount + 1 - i).map((num) => (
              <option key={num} value={num}>
                {t("dataCleansing.detail.logTable.currentDisplay", { num: num })}
              </option>
            ))}
          </select>
          {isStreaming && (
            <span className="text-xs text-blue-400 animate-pulse">{t("dataCleansing.detail.logTable.streaming")}</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-s text-gray-500 px-2">{t("dataCleansing.detail.logTable.nthRun", { num: selectedLog })}</span>
          <button
            onClick={handleDownload}
            disabled={isStreaming}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 border border-blue-500 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            <Download className="w-4 h-4" />
            <span>{t("dataCleansing.detail.logTable.download")}</span>
          </button>
        </div>
      </div>
      <div className="text-gray-300 p-4 border border-gray-700 bg-gray-800 rounded-lg">
        <div className="font-mono text-sm">
          <VirtualList
            data={logsWithIndex}
            height={580}
            itemHeight={22}
            itemKey="index"
          >
            {(log: LogEntryWithIndex) => (
              <div className="flex gap-3 py-0.5">
                <span className={`min-w-20 ${getLevelClass(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="text-gray-100">{log.message}</span>
              </div>
            )}
          </VirtualList>
          {isStreaming && (
            <div className="flex gap-3 animate-pulse py-0.5">
              <span className="text-gray-400">...</span>
            </div>
          )}
        </div>
      </div>
    </>
  ) : (
    <div className="text-center py-12">
      <FileClock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {t("dataCleansing.detail.logTable.noLogs")}
      </h3>
    </div>
  );
}
