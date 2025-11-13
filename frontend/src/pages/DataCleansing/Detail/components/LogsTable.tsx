import {useEffect} from "react";
import {useParams} from "react-router";
import {FileClock} from "lucide-react";

export default function LogsTable({taskLog, fetchTaskLog} : {taskLog: any[], fetchTaskLog: () => Promise<any>}) {
  const { id = "" } = useParams();

  useEffect(() => {
    fetchTaskLog();
  }, [id]);

  return taskLog?.length > 0 ? (
    <>
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
