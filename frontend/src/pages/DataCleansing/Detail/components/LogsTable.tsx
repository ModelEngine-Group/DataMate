import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router";
import { FileClock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { streamCleaningTaskLog } from "../../cleansing.api";

interface LogEntry {
  level: string;
  message: string;
}

export default function LogsTable({ taskLog: initialLogs, fetchTaskLog, retryCount }: { taskLog: any[], fetchTaskLog: () => Promise<any>, retryCount: number }) {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const [selectedLog, setSelectedLog] = useState(retryCount + 1);
  const [streamingLogs, setStreamingLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (selectedLog - 1 === retryCount) {
      startStreaming();
    } else {
      stopStreaming();
      fetchTaskLog(selectedLog - 1);
    }
    return () => stopStreaming();
  }, [id, selectedLog, retryCount]);

  useEffect(() => {
    if (logContainerRef.current && isStreaming) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [streamingLogs, isStreaming]);

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
            stopStreaming();
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

  const displayLogs = selectedLog - 1 === retryCount ? streamingLogs : initialLogs;

  const handleSelectChange = (value: number) => {
    setSelectedLog(value);
    setStreamingLogs([]);
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
        <span className="text-s text-gray-500 px-2">{t("dataCleansing.detail.logTable.nthRun", { num: selectedLog })}</span>
      </div>
      <div className="text-gray-300 p-4 border border-gray-700 bg-gray-800 rounded-lg">
        <div
          ref={logContainerRef}
          className="font-mono text-sm max-h-[600px] overflow-y-auto"
        >
          {displayLogs?.map?.((log, index) => (
            <div key={index} className="flex gap-3">
              <span
                className={`min-w-20 ${
                  log.level === "ERROR" || log.level === "FATAL"
                    ? "text-red-500"
                    : log.level === "WARNING" || log.level === "WARN"
                      ? "text-yellow-500"
                      : "text-green-500"
                }`}
              >
                [{log.level}]
              </span>
              <span className="text-gray-100">{log.message}</span>
            </div>
          ))}
          {isStreaming && (
            <div className="flex gap-3 animate-pulse">
              <span className="min-w-20 text-blue-400">[INFO]</span>
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
