import { Button, Card, Badge, Breadcrumb } from "antd";
import {
  ArrowLeft,
  Download,
  Users,
  Scissors,
  BarChart3,
  Target,
  Calendar,
  TrendingUp,
  MessageSquare,
  Star,
} from "lucide-react";
import {
  mockQAPairs,
  mockTasks,
  presetEvaluationDimensions,
} from "@/mock/evaluation";
import { Link, useNavigate } from "react-router";

const EvaluationTaskReport = () => {
  const navigate = useNavigate();
  const selectedTask = mockTasks[0]; // 假设我们只展示第一个任务的报告

  // 获取任务的所有维度
  const getTaskAllDimensions = (task: EvaluationTask) => {
    const presetDimensions = presetEvaluationDimensions.filter((d) =>
      task.dimensions.includes(d.id)
    );
    return [...presetDimensions, ...(task.customDimensions || [])];
  };
  const allDimensions = getTaskAllDimensions(selectedTask);

  return (
    <div className="min-h-screen">
      <div className="mx-auto space-y-2">
        {/* 头部 */}
        <div className="flex items-center justify-between">
          <Breadcrumb
            items={[
              {
                title: <Link to="/data/evaluation">数据评估</Link>,
              },
              { title: "评估报告", key: "report" },
            ]}
          ></Breadcrumb>
          <div className="flex items-center gap-2">
            <Button
              className="flex items-center gap-2"
              icon={<Download className="w-4 h-4" />}
            >
              导出报告
            </Button>
          </div>
        </div>

        {/* 基本信息卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedTask.score || 0}
                  </div>
                  <div className="text-sm text-gray-500">总体评分</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Target className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedTask.sliceConfig?.sampleCount}
                  </div>
                  <div className="text-sm text-gray-500">评估样本数</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedTask.evaluationType === "manual" ? "人工" : "模型"}
                  </div>
                  <div className="text-sm text-gray-500">评估方式</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Calendar className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedTask.progress}%
                  </div>
                  <div className="text-sm text-gray-500">完成进度</div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 详细信息 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 评估结果 */}
          <Card
            title={
              <span className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                评估结果
              </span>
            }
            bodyStyle={{ paddingTop: 0 }}
          >
            {/* 维度评分 */}
            <div className="mt-4">
              <h4 className="font-medium mb-3">维度评分</h4>
              <div className="space-y-3">
                {allDimensions.map((dimension) => {
                  const score = 75 + Math.floor(Math.random() * 20); // 模拟评分
                  return (
                    <div
                      key={dimension.id}
                      className="flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">
                            {dimension.name}
                          </span>
                          <span className="text-sm font-bold text-blue-600">
                            {score}分
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 质量分数解读 */}
            <div className="border-t pt-4 mt-4">
              <h4 className="font-medium mb-3">质量分数解读</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                  <span>90-100分: 优秀，质量很高</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full" />
                  <span>80-89分: 良好，质量较好</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                  <span>70-79分: 一般，需要改进</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full" />
                  <span>60-69分: 较差，需要重点关注</span>
                </div>
              </div>
            </div>
          </Card>

          {/* 切片信息 */}
          <Card
            title={
              <span className="flex items-center gap-2">
                <Scissors className="w-5 h-5" />
                切片信息
              </span>
            }
            bodyStyle={{ paddingTop: 0 }}
          >
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">切片阈值:</span>
                  <span className="ml-2 font-medium">
                    {selectedTask.sliceConfig?.threshold}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">抽样数量:</span>
                  <span className="ml-2 font-medium">
                    {selectedTask.sliceConfig?.sampleCount}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">切片方法:</span>
                  <span className="ml-2 font-medium">
                    {selectedTask.sliceConfig?.method}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">评估时间:</span>
                  <span className="ml-2 font-medium">
                    {selectedTask.completedAt || selectedTask.createdAt}
                  </span>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">评估维度</h4>
                <div className="flex flex-wrap gap-2">
                  {allDimensions.map((dimension) => (
                    <Badge
                      key={dimension.id}
                      style={{
                        border: "1px solid #d9d9d9",
                        background: "#fafafa",
                        padding: "0 8px",
                      }}
                    >
                      {dimension.name}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* QA对详情 */}
        <Card
          title={
            <span className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              QA对详情
            </span>
          }
          bodyStyle={{ paddingTop: 0 }}
        >
          <div className="space-y-4 mt-4">
            {mockQAPairs.map((qa) => (
              <div key={qa.id} className="border rounded-lg p-4">
                <div className="space-y-3">
                  <div>
                    <span className="text-sm font-medium text-gray-700 mb-1">
                      问题:
                    </span>
                    <span className="text-gray-900">{qa.question}</span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-700 mb-1">
                      回答:
                    </span>
                    <span className="text-gray-900">{qa.answer}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">评分:</span>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            className={`w-4 h-4 ${
                              star <= qa.score
                                ? "text-yellow-400"
                                : "text-gray-300"
                            }`}
                            style={star <= qa.score ? { fill: "#facc15" } : {}}
                          />
                        ))}
                      </div>
                      <span className="text-sm font-medium">{qa.score}/5</span>
                    </div>
                    {qa.feedback && (
                      <div className="text-sm text-gray-600">{qa.feedback}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default EvaluationTaskReport;
