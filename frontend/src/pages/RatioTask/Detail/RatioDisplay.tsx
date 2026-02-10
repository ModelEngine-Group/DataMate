import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useTranslation } from "react-i18next";

interface DatasetRatio {
  name: string;
  ratio: number;
  count: number;
  color: string;
}

export default function RatioDisplay() {
  const { t } = useTranslation();
  const datasets: DatasetRatio[] = [
    { name: t("ratioTask.detail.ratioDisplay.datasetUserBehavior"), ratio: 45, count: 450000, color: "#3b82f6" },
    { name: t("ratioTask.detail.ratioDisplay.datasetTransaction"), ratio: 30, count: 300000, color: "#8b5cf6" },
    { name: t("ratioTask.detail.ratioDisplay.datasetProduct"), ratio: 15, count: 150000, color: "#ec4899" },
    { name: t("ratioTask.detail.ratioDisplay.datasetReview"), ratio: 10, count: 100000, color: "#f59e0b" },
  ];

  const chartData = datasets.map((d) => ({
    name: d.name,
    value: d.ratio,
    count: d.count,
    fill: d.color,
  }));

  return (
    <div className="mt-8">
      <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
        {t("ratioTask.detail.ratioDisplay.title")}
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 饼图展示比例 */}
        <div className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 数据集详情列表 */}
        <div className="space-y-4">
          {datasets.map((dataset, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: dataset.color }}
                  ></div>
                  <span className="font-medium text-foreground text-sm">
                    {dataset.name}
                  </span>
                </div>
                <span className="text-sm font-semibold text-foreground">
                  {dataset.ratio}%
                </span>
              </div>

              {/* 比例条形图 */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${dataset.ratio}%`,
                      backgroundColor: dataset.color,
                    }}
                  ></div>
                </div>
                <span className="text-xs text-muted-foreground min-w-fit">
                  {dataset.count.toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
