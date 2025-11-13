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

const chartData = [
  { name: "一月", 配比率: 65, 成功数: 2400, 失败数: 240 },
  { name: "二月", 配比率: 72, 成功数: 2210, 失败数: 221 },
  { name: "三月", 配比率: 78, 成功数: 2290, 失败数: 229 },
  { name: "四月", 配比率: 84, 成功数: 2000, 失败数: 200 },
  { name: "五月", 配比率: 90, 成功数: 2181, 失败数: 218 },
  { name: "六月", 配比率: 94, 成功数: 2500, 失败数: 250 },
]

export default function DataRatioChart() {
  return (
    <div className="lg:col-span-3 space-y-6">
      <div className="border-border bg-card/50 backdrop-blur p-6">
        <h3 className="text-base font-semibold text-foreground mb-4">配比趋势分析</h3>
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
            />
            <Legend />
            <Bar dataKey="成功数" stackId="a" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            <Bar dataKey="失败数" stackId="a" fill="#ef4444" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="border-border bg-card/50 backdrop-blur p-6">
        <h3 className="text-base font-semibold text-foreground mb-4">成功率曲线</h3>
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
            />
            <Line
              type="monotone"
              dataKey="配比率"
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
