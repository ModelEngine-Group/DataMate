import type React from "react"
import { useState } from "react"
import { Card, Button, Modal, Empty, Spin, Progress } from "antd"
import { Cloud, Power, Trash2, AlertCircle, CheckCircle, Clock, Terminal, Copy, RefreshCw } from "lucide-react"

interface Pod {
  id: string
  name: string
  status: "running" | "pending" | "failed" | "terminated"
  cpuUsage: number
  memoryUsage: number
  restarts: number
  createdAt: string
}

interface ServiceDeployment {
  status: "not_deployed" | "deploying" | "deployed" | "failed"
  deployedAt?: string
  version?: string
  replicas: number
  pods: Pod[]
}

interface OperatorServiceMonitorProps {
  operatorName: string
  supportsService?: boolean
}

export default function OperatorServiceMonitor({
                                                 operatorName,
                                                 supportsService = true,
                                               }: OperatorServiceMonitorProps) {
  const [serviceDeployment, setServiceDeployment] = useState<ServiceDeployment>({
    status: "not_deployed",
    replicas: 0,
    pods: [],
  })

  const [isDeploying, setIsDeploying] = useState(false)
  const [selectedPod, setSelectedPod] = useState<Pod | null>(null)
  const [showLogModal, setShowLogModal] = useState(false)
  const [deploymentError, setDeploymentError] = useState<string | null>(null)

  // 模拟部署
  const handleDeploy = async () => {
    if (!supportsService) {
      setDeploymentError(`${operatorName} 算子不支持服务部署`)
      return
    }

    setIsDeploying(true)
    setDeploymentError(null)

    // 模拟部署过程
    setTimeout(() => {
      setServiceDeployment({
        status: "deployed",
        deployedAt: new Date().toISOString(),
        version: "1.2.0",
        replicas: 3,
        pods: [
          {
            id: "1",
            name: `${operatorName}-pod-1`,
            status: "running",
            cpuUsage: 45,
            memoryUsage: 62,
            restarts: 0,
            createdAt: new Date(Date.now() - 3600000).toISOString(),
          },
          {
            id: "2",
            name: `${operatorName}-pod-2`,
            status: "running",
            cpuUsage: 38,
            memoryUsage: 58,
            restarts: 1,
            createdAt: new Date(Date.now() - 7200000).toISOString(),
          },
          {
            id: "3",
            name: `${operatorName}-pod-3`,
            status: "running",
            cpuUsage: 52,
            memoryUsage: 68,
            restarts: 0,
            createdAt: new Date(Date.now() - 1800000).toISOString(),
          },
        ],
      })
      setIsDeploying(false)
    }, 2000)
  }

  // 模拟卸载
  const handleUndeploy = () => {
    Modal.confirm({
      title: "确认卸载服务",
      content: `确定要卸载 ${operatorName} 的服务吗？这将停止所有运行中的Pod实例。`,
      okText: "卸载",
      okType: "danger",
      cancelText: "取消",
      onOk() {
        setServiceDeployment({
          status: "not_deployed",
          replicas: 0,
          pods: [],
        })
      },
    })
  }

  // 获取状态样式
  const getStatusConfig = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
      running: {
        color: "bg-green-100 text-green-800 border-green-200",
        icon: <CheckCircle className="w-4 h-4" />,
        label: "运行中",
      },
      pending: {
        color: "bg-yellow-100 text-yellow-800 border-yellow-200",
        icon: <Clock className="w-4 h-4" />,
        label: "待机中",
      },
      failed: {
        color: "bg-red-100 text-red-800 border-red-200",
        icon: <AlertCircle className="w-4 h-4" />,
        label: "失败",
      },
      terminated: {
        color: "bg-gray-100 text-gray-800 border-gray-200",
        icon: <Power className="w-4 h-4" />,
        label: "已停止",
      },
    }
    return config[status] || config.pending
  }

  const renderNotDeployed = () => (
    <div className="text-center py-12">
      <Cloud className="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">服务未部署</h3>
      <p className="text-gray-600 mb-6">点击下方按钮部署 {operatorName} 服务</p>
      <Button type="primary" size="large" loading={isDeploying} onClick={handleDeploy} disabled={!supportsService}>
        <Power className="w-4 h-4 mr-2" />
        部署服务
      </Button>
      {!supportsService && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 inline mr-2" />
          该算子不支持服务部署
        </div>
      )}
    </div>
  )

  const renderDeployed = () => (
    <div className="space-y-6">
      {/* 部署信息 */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">部署信息</h3>
            <div className="space-y-1 text-sm text-gray-600">
              <div>部署时间: {new Date(serviceDeployment.deployedAt!).toLocaleString("zh-CN")}</div>
              <div>版本: {serviceDeployment.version}</div>
              <div>副本数: {serviceDeployment.replicas}</div>
            </div>
          </div>
          <Button danger onClick={handleUndeploy}>
            <Trash2 className="w-4 h-4 mr-2" />
            卸载服务
          </Button>
        </div>
      </Card>

      {/* Pod 监控 */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Pod 实例监控</h3>
          <Button type="text" size="small">
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>
        </div>

        {serviceDeployment.pods.length === 0 ? (
          <Empty description="暂无Pod实例" />
        ) : (
          <div className="space-y-3">
            {serviceDeployment.pods.map((pod) => {
              const statusConfig = getStatusConfig(pod.status)
              return (
                <Card key={pod.id} className="border-l-4 border-l-blue-500 bg-gray-50">
                  <div className="space-y-3">
                    {/* Pod 基本信息 */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{pod.name}</div>
                          <div className="text-xs text-gray-500">
                            创建时间: {new Date(pod.createdAt).toLocaleString("zh-CN")}
                          </div>
                        </div>
                      </div>
                      <div
                        className={`flex items-center gap-1 px-3 py-1 rounded-full border text-xs font-medium ${statusConfig.color}`}
                      >
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                      </div>
                    </div>

                    {/* 资源使用情况 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-xs text-gray-600 mb-1">CPU 使用率</div>
                        <div className="flex items-center gap-2">
                          <Progress
                            type="circle"
                            percent={pod.cpuUsage}
                            width={40}
                            strokeColor={pod.cpuUsage > 80 ? "#ef4444" : "#10b981"}
                          />
                          <span className="text-sm font-medium text-gray-900">{pod.cpuUsage}%</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-600 mb-1">内存使用率</div>
                        <div className="flex items-center gap-2">
                          <Progress
                            type="circle"
                            percent={pod.memoryUsage}
                            width={40}
                            strokeColor={pod.memoryUsage > 80 ? "#ef4444" : "#3b82f6"}
                          />
                          <span className="text-sm font-medium text-gray-900">{pod.memoryUsage}%</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-center">
                          <div className="text-xs text-gray-600">重启次数</div>
                          <div className="text-lg font-semibold text-gray-900">{pod.restarts}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 justify-end">
                        <Button
                          type="text"
                          size="small"
                          onClick={() => {
                            setSelectedPod(pod)
                            setShowLogModal(true)
                          }}
                        >
                          <Terminal className="w-4 h-4 mr-1" />
                          查看日志
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* 错误提示 */}
      {deploymentError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{deploymentError}</span>
        </div>
      )}

      {/* 主要内容 */}
      {isDeploying ? (
        <Card className="text-center py-12">
          <Spin size="large" />
          <p className="mt-4 text-gray-600">正在部署服务...</p>
        </Card>
      ) : serviceDeployment.status === "not_deployed" ? (
        <Card>{renderNotDeployed()}</Card>
      ) : (
        renderDeployed()
      )}

      {/* Pod 日志模态框 */}
      <Modal
        title={`${selectedPod?.name} - 日志`}
        open={showLogModal}
        onCancel={() => setShowLogModal(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setShowLogModal(false)}>
            关闭
          </Button>,
          <Button
            key="copy"
            type="primary"
            onClick={() => {
              const logs = `[INFO] 2024-01-24 10:30:45.123 - Pod started successfully
[INFO] 2024-01-24 10:30:46.456 - Loading model weights...
[INFO] 2024-01-24 10:30:52.789 - Model loaded successfully
[INFO] 2024-01-24 10:30:53.012 - Service initialized on port 8080
[DEBUG] 2024-01-24 10:31:00.345 - Received request: /predict
[INFO] 2024-01-24 10:31:01.678 - Processing image: input.jpg
[INFO] 2024-01-24 10:31:02.901 - Prediction completed: class=cat, confidence=0.95
[DEBUG] 2024-01-24 10:31:03.234 - Response sent successfully`
              navigator.clipboard.writeText(logs)
            }}
          >
            <Copy className="w-4 h-4 mr-2" />
            复制日志
          </Button>,
        ]}
      >
        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-y-auto max-h-96">
          <div className="space-y-1">
            <div>[INFO] 2024-01-24 10:30:45.123 - Pod started successfully</div>
            <div>[INFO] 2024-01-24 10:30:46.456 - Loading model weights...</div>
            <div>[INFO] 2024-01-24 10:30:52.789 - Model loaded successfully</div>
            <div>[INFO] 2024-01-24 10:30:53.012 - Service initialized on port 8080</div>
            <div className="text-blue-400">[DEBUG] 2024-01-24 10:31:00.345 - Received request: /predict</div>
            <div>[INFO] 2024-01-24 10:31:01.678 - Processing image: input.jpg</div>
            <div className="text-green-400">
              [INFO] 2024-01-24 10:31:02.901 - Prediction completed: class=cat, confidence=0.95
            </div>
            <div className="text-blue-400">[DEBUG] 2024-01-24 10:31:03.234 - Response sent successfully</div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
