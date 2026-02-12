import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts"
import { useTranslation } from "react-i18next"
import { useMemo } from "react"

export default function DataRatioChart() {
  const { t } = useTranslation()
  const chartData = useMemo(
    () => [
      { name: t("ratioTask.detail.chart.monthJan"), ratioRate: 65, successCount: 2400, failCount: 240 },
      { name: t("ratioTask.detail.chart.monthFeb"), ratioRate: 72, successCount: 2210, failCount: 221 },
      { name: t("ratioTask.detail.chart.monthMar"), ratioRate: 78, successCount: 2290, failCount: 229 },
      { name: t("ratioTask.detail.chart.monthApr"), ratioRate: 84, successCount: 2000, failCount: 200 },
      { name: t("ratioTask.detail.chart.monthMay"), ratioRate: 90, successCount: 2181, failCount: 218 },
      { name: t("ratioTask.detail.chart.monthJun"), ratioRate: 94, successCount: 2500, failCount: 250 },
    ],
    [t]
  )
  const legendFormatter = (value: string) => {
    const keyMap: Record<string, string> = {
      ratioRate: t("ratioTask.detail.chart.ratioRate"),
      successCount: t("ratioTask.detail.chart.successCount"),
      failCount: t("ratioTask.detail.chart.failCount"),
    }
    return keyMap[value] ?? value
  }
  return (
    <div className="lg:col-span-3 space-y-6">
      <div className="border-border bg-card/50 backdrop-blur p-6">
        <h3 className="text-base font-semibold text-foreground mb-4">{t("ratioTask.detail.chart.ratioTrendTitle")}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
            <XAxis dataKey="name" stroke="rgb(var(--muted-foreground))" />
            <YAxis stroke="rgb(var(--muted-foreground))" />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgb(var(--card))",
                border: "1px solid rgb(var(--border))",
                borderRadius: "8px",
              }}
              cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
              formatter={(value: number, name: string) => [value, legendFormatter(name)]}
            />
            <Legend formatter={legendFormatter} />
            <Bar dataKey="successCount" stackId="a" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            <Bar dataKey="failCount" stackId="a" fill="#ef4444" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="border-border bg-card/50 backdrop-blur p-6">
        <h3 className="text-base font-semibold text-foreground mb-4">{t("ratioTask.detail.chart.successRateCurve")}</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
            <XAxis dataKey="name" stroke="rgb(var(--muted-foreground))" />
            <YAxis stroke="rgb(var(--muted-foreground))" />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgb(var(--card))",
                border: "1px solid rgb(var(--border))",
                borderRadius: "8px",
              }}
              cursor={{ stroke: "rgba(34, 197, 94, 0.2)" }}
              formatter={(value: number, name: string) => [value, legendFormatter(name)]}
            />
            <Line
              type="monotone"
              dataKey="ratioRate"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ fill: "#22c55e", r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
