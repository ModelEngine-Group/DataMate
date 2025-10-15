export default function LogsTable({ task }: { task: any }) {
  // 模拟运行日志
  const runLogs = [
    {
      time: "09:30:15",
      level: "INFO",
      message: "开始执行数据清洗任务: 肺癌WSI图像清洗任务",
    },
    {
      time: "09:30:16",
      level: "INFO",
      message: "加载源数据集: 肺癌WSI病理图像数据集 (1250 文件)",
    },
    { time: "09:30:17", level: "INFO", message: "初始化算子: 格式转换" },
    {
      time: "09:30:18",
      level: "INFO",
      message: "开始处理文件: lung_cancer_001.svs",
    },
    {
      time: "09:30:25",
      level: "SUCCESS",
      message: "文件处理成功: lung_cancer_001.svs -> lung_cancer_001.jpg",
    },
    {
      time: "09:30:26",
      level: "INFO",
      message: "开始处理文件: lung_cancer_002.svs",
    },
    {
      time: "09:30:33",
      level: "SUCCESS",
      message: "文件处理成功: lung_cancer_002.svs -> lung_cancer_002.jpg",
    },
    {
      time: "09:58:42",
      level: "INFO",
      message: "格式转换完成，成功处理 1250/1250 文件",
    },
    { time: "09:58:43", level: "INFO", message: "初始化算子: 噪声去除" },
    {
      time: "09:58:44",
      level: "INFO",
      message: "开始处理文件: lung_cancer_001.jpg",
    },
    {
      time: "09:58:51",
      level: "SUCCESS",
      message: "噪声去除成功: lung_cancer_001.jpg",
    },
    {
      time: "10:15:23",
      level: "WARNING",
      message: "文件质量较低，跳过处理: lung_cancer_156.jpg",
    },
    {
      time: "10:35:18",
      level: "INFO",
      message: "噪声去除完成，成功处理 1228/1250 文件",
    },
    { time: "10:35:19", level: "INFO", message: "初始化算子: 尺寸标准化" },
    {
      time: "11:12:05",
      level: "INFO",
      message: "尺寸标准化完成，成功处理 1222/1228 文件",
    },
    { time: "11:12:06", level: "INFO", message: "初始化算子: 质量检查" },
    {
      time: "11:25:33",
      level: "ERROR",
      message: "质量检查失败: lung_cancer_089.jpg - 分辨率过低",
    },
    {
      time: "11:45:32",
      level: "INFO",
      message: "质量检查完成，成功处理 1198/1222 文件",
    },
    {
      time: "11:45:33",
      level: "SUCCESS",
      message: "数据清洗任务完成！总成功率: 95.8%",
    },
  ];

  return (
    <div className="text-gray-300 p-4 border border-gray-700 bg-gray-800 rounded-lg">
      <div className="font-mono text-sm">
        {runLogs?.map?.((log, index) => (
          <div key={index} className="flex gap-3">
            <span className="text-gray-500 min-w-20">{log.time}</span>
            <span
              className={`min-w-20 ${
                log.level === "ERROR"
                  ? "text-red-500"
                  : log.level === "WARNING"
                  ? "text-yellow-500"
                  : log.level === "SUCCESS"
                  ? "text-green-500"
                  : "text-blue-500"
              }`}
            >
              [{log.level}]
            </span>
            <span className="text-gray-100">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
