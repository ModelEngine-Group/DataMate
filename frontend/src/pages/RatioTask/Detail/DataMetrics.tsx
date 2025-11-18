import { Card } from "antd"
import { BarChart3, Database, Users, Zap } from "lucide-react"

const metrics = [
  {
    label: "总数据量",
    value: "2.5M",
    icon: Database,
    change: "+12.5%",
    color: "text-blue-400",
  },
  {
    label: "配比成功率",
    value: "94.2%",
    icon: BarChart3,
    change: "+2.1%",
    color: "text-emerald-400",
  },
  {
    label: "处理速度",
    value: "185K/s",
    icon: Zap,
    change: "+8.3%",
    color: "text-amber-400",
  },
  {
    label: "活跃用户",
    value: "156.8K",
    icon: Users,
    change: "+5.2%",
    color: "text-purple-400",
  },
]

export default function DataMetrics() {
  return (
    <div className="border-card grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
      {metrics.map((metric, idx) => {
        const Icon = metric.icon
        return (
          <div
            key={idx}
            className="border-border bg-card/50 backdrop-blur p-4 hover:bg-card/70 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg bg-muted/50 ${metric.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-xs font-medium text-emerald-400">{metric.change}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-1">{metric.label}</p>
            <p className="text-2xl font-bold text-foreground">{metric.value}</p>
          </div>
        )
      })}
    </div>
  )
}
