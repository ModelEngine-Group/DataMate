import { Button, Popover, Progress } from "antd";
import { Calendar, Clock, Play, Trash2, X } from "lucide-react";

interface TaskItem {
  id: string;
  name: string;
  status: string;
  progress: number;
  scheduleConfig: {
    type: string;
    cronExpression?: string;
    executionCount?: number;
    maxExecutions?: number;
  };
  nextExecution?: string;
  importConfig: {
    source?: string;
  };
  createdAt: string;
}

export default function TaskPopover() {
  const tasks: TaskItem[] = [
    {
      id: "1",
      name: "导入客户数据",
      status: "importing",
      progress: 65,
      scheduleConfig: {
        type: "manual",
      },
      importConfig: {
        source: "local",
      },
      createdAt: "2025-07-29 14:23",
    },
    {
      id: "2",
      name: "定时同步订单",
      status: "waiting",
      progress: 0,
      scheduleConfig: {
        type: "scheduled",
        cronExpression: "0 0 * * *",
        executionCount: 3,
        maxExecutions: 10,
      },
      nextExecution: "2025-07-31 00:00",
      importConfig: {
        source: "api",
      },
      createdAt: "2025-07-28 09:10",
    },
    {
      id: "3",
      name: "清理历史日志",
      status: "finished",
      progress: 100,
      scheduleConfig: {
        type: "manual",
      },
      importConfig: {
        source: "system",
      },
      createdAt: "2025-07-27 17:45",
    },
  ];

  return (
    <Popover
      placement="topLeft"
      content={
        <div className="w-[500px]">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">近期任务</h3>
            <Button type="text" className="h-6 w-6 p-0">
              <X className="w-4 h-4 text-black-400 hover:text-gray-500" />
            </Button>
          </div>

          <div className="p-2">
            {tasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Clock className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">暂无创建任务</p>
              </div>
            ) : (
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="p-3 border border-gray-100 rounded-lg hover:bg-gray-50"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm truncate flex-1">
                          {task.name}
                        </h4>
                        <div className="flex items-center gap-2">
                          {task.status === "waiting" && (
                            <Button
                              className="h-6 w-6 p-0 text-blue-500 hover:text-blue-700"
                              title="立即执行"
                            >
                              <Play className="w-3 h-3" />
                            </Button>
                          )}
                          <Button className="h-6 w-6 p-0 text-gray-400 hover:text-red-500">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>

                      {task.status === "importing" && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>导入进度</span>
                            <span>{Math.round(task.progress)}%</span>
                          </div>
                          <Progress percent={task.progress} />
                        </div>
                      )}

                      {/* Schedule Information */}
                      {task.scheduleConfig.type === "scheduled" && (
                        <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                          <div className="flex items-center gap-1 mb-1">
                            <Calendar className="w-3 h-3" />
                            <span className="font-medium">定时任务</span>
                          </div>
                          <div>Cron: {task.scheduleConfig.cronExpression}</div>
                          {task.nextExecution && (
                            <div>下次执行: {task.nextExecution}</div>
                          )}
                          <div>
                            执行次数: {task.scheduleConfig.executionCount || 0}/
                            {task.scheduleConfig.maxExecutions || 10}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>
                          {task.importConfig.source === "local"
                            ? "本地上传"
                            : task.importConfig.source || "未知来源"}
                        </span>
                        <span>{task.createdAt}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      }
    >
      <Button block>任务中心</Button>
    </Popover>
  );
}
