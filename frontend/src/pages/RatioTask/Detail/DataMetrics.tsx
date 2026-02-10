import { BarChart3, Database, Users, Zap } from "lucide-react"
import { useTranslation } from "react-i18next"

export default function DataMetrics() {
  const { t } = useTranslation()
  const metrics = [
    {
      label: t("ratioTask.detail.metrics.totalData"),
      value: "2.5M",
      icon: Database,
      change: "+12.5%",
      color: "text-blue-400",
    },
    {
      label: t("ratioTask.detail.metrics.ratioSuccessRate"),
      value: "94.2%",
      icon: BarChart3,
      change: "+2.1%",
      color: "text-emerald-400",
    },
    {
      label: t("ratioTask.detail.metrics.processSpeed"),
      value: "185K/s",
      icon: Zap,
      change: "+8.3%",
      color: "text-amber-400",
    },
    {
      label: t("ratioTask.detail.metrics.activeUsers"),
      value: "156.8K",
      icon: Users,
      change: "+5.2%",
      color: "text-purple-400",
    },
  ]
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
