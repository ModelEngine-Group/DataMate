import {useEffect, useState} from "react";
import {useParams} from "react-router";
import {FileClock} from "lucide-react";

export default function LogsTable({taskLog, fetchTaskLog, retryCount} : {taskLog: any[], fetchTaskLog: () => Promise<any>, retryCount: number}) {
  const { id = "" } = useParams();
  const [selectedLog, setSelectedLog] = useState(retryCount + 1);

  useEffect(() => {
    fetchTaskLog(selectedLog - 1);
  }, [id, selectedLog]);

  return taskLog?.length > 0 ? (
    <>
      {/* --- 新增区域：左上角 Select 组件 --- */}
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-500">选择运行轮次:</label>
          <select
            value={selectedLog}
            onChange={(e) => setSelectedLog(Number(e.target.value))}
            className="bg-gray-700 border border-gray-600 !text-white text-sm rounded-md focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1.5 min-w-[120px]"
          >
            {Array.from({ length: retryCount + 1 }, (_, i) => retryCount + 1 - i).map((num) => (
              <option key={num} value={num}>
                第 {num} 次
              </option>
            ))}
          </select>
        </div>
        <span className="text-s text-gray-500 px-2">当前展示: 第 {selectedLog} 次</span>
      </div>
      <div className="text-gray-300 p-4 border border-gray-700 bg-gray-800 rounded-lg">
        <div className="font-mono text-sm">
          {taskLog?.map?.((log, index) => (
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
        </div>
      </div>
    </>
  ) : (
    <div className="text-center py-12">
      <FileClock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        当前任务无可用日志
      </h3>
    </div>
  );
}
