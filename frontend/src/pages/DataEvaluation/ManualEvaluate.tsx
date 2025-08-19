"use client";

import { useState, useEffect } from "react";
import { Button, Card, Badge, Input, Typography } from "antd";
import {
  LeftOutlined,
  RightOutlined,
  SaveOutlined,
  ScissorOutlined,
  AimOutlined,
  CalendarOutlined,
  FileTextOutlined,
  StarFilled,
  DatabaseOutlined,
} from "@ant-design/icons";
import { mockTasks, presetEvaluationDimensions } from "@/mock/evaluation";
import { useNavigate } from "react-router";

const { TextArea } = Input;
const { Title } = Typography;

// 生成切片内容
const generateSliceContent = (index: number) => {
  const contents = [
    "用户咨询产品退换货政策的相关问题，希望了解具体的退货流程和时间限制。客服详细解释了7天无理由退货政策，包括商品需要保持原包装完整的要求。这个回答涵盖了用户关心的主要问题，提供了明确的时间限制和条件说明。",
    "客服回复关于质量问题商品的处理方式，说明15天内免费换货服务，并承诺承担相关物流费用。用户对此表示满意，认为这个政策很合理。回答中明确区分了质量问题和非质量问题的不同处理方式。",
    "用户询问特殊商品的退换货政策，客服解释个人定制商品不支持退货的规定，并建议用户在购买前仔细确认商品信息。这个回答帮助用户理解了特殊商品的限制条件。",
    "关于退货流程的详细说明，客服介绍了在线申请退货的步骤，包括订单页面操作和快递上门取件服务。整个流程描述清晰，用户可以轻松按照步骤操作。",
    "用户对物流费用承担问题提出疑问，客服明确说明质量问题导致的退换货由公司承担物流费用，非质量问题由用户承担。这个回答消除了用户的疑虑。",
  ];
  return contents[index % contents.length];
};

const slices: EvaluationSlice[] = Array.from(
  { length: mockTasks[0].sliceConfig?.sampleCount || 50 },
  (_, index) => ({
    id: `slice_${index + 1}`,
    content: generateSliceContent(index),
    sourceFile: `file_${Math.floor(index / 5) + 1}.txt`,
    sliceIndex: index % 5,
    sliceType: ["paragraph", "sentence", "semantic"][index % 3],
    metadata: {
      startPosition: index * 200,
      endPosition: (index + 1) * 200,
      pageNumber: Math.floor(index / 10) + 1,
      section: `Section ${Math.floor(index / 5) + 1}`,
      processingMethod: mockTasks[0].sliceConfig?.method || "语义分割",
    },
  })
);

const ManualEvaluatePage = ({ taskId }) => {
  const navigate = useNavigate();
  // 人工评估状态
  const [currentEvaluationTask, setCurrentEvaluationTask] =
    useState<EvaluationTask | null>(mockTasks[0]);
  const [evaluationSlices, setEvaluationSlices] =
    useState<EvaluationSlice[]>(slices);
  const [currentSliceIndex, setCurrentSliceIndex] = useState(0);
  const [sliceScores, setSliceScores] = useState<{
    [key: string]: { [dimensionId: string]: number };
  }>({});
  const [sliceComments, setSliceComments] = useState<{ [key: string]: string }>(
    {}
  );

  const currentSlice = evaluationSlices[currentSliceIndex];
  const currentScores = sliceScores[currentSlice?.id] || {};
  const progress =
    evaluationSlices.length > 0
      ? ((currentSliceIndex + 1) / evaluationSlices.length) * 100
      : 0;

  // 获取任务的所有维度
  const getTaskAllDimensions = (task: EvaluationTask) => {
    const presetDimensions = presetEvaluationDimensions.filter((d) =>
      task.dimensions.includes(d.id)
    );
    return [...presetDimensions, ...(task.customDimensions || [])];
  };

  const allDimensions = getTaskAllDimensions(mockTasks[0]);

  // 更新切片评分
  const updateSliceScore = (
    sliceId: string,
    dimensionId: string,
    score: number
  ) => {
    setSliceScores((prev) => ({
      ...prev,
      [sliceId]: {
        ...prev[sliceId],
        [dimensionId]: score,
      },
    }));
  };

  // 保存当前切片评分并进入下一个
  const handleSaveAndNext = () => {
    const currentSlice = evaluationSlices[currentSliceIndex];
    if (!currentSlice) return;

    // 检查是否所有维度都已评分
    const allDimensions = getTaskAllDimensions(currentEvaluationTask!);
    const currentScores = sliceScores[currentSlice.id] || {};
    const hasAllScores = allDimensions.every(
      (dim) => currentScores[dim.id] > 0
    );

    if (!hasAllScores) {
      window.alert("请为所有维度评分后再保存");
      return;
    }

    // 如果是最后一个切片，完成评估
    if (currentSliceIndex === evaluationSlices.length - 1) {
      handleCompleteEvaluation();
    } else {
      setCurrentSliceIndex(currentSliceIndex + 1);
    }
  };

  // 完成评估
  const handleCompleteEvaluation = () => {
    // 计算平均分
    const allScores = Object.values(sliceScores).flatMap((scores) =>
      Object.values(scores)
    );
    // const averageScore = allScores.length > 0 ? Math.round((allScores.reduce((a, b) => a + b, 0) / allScores.length) * 20) : 0
    navigate(`/data/evaluation/task-report/${mockTasks[0].id}`);
  };

  // 星星评分组件
  const StarRating = ({
    value,
    onChange,
    dimension,
  }: {
    value: number;
    onChange: (value: number) => void;
    dimension: EvaluationDimension;
  }) => {
    return (
      <div style={{ marginBottom: 8 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontWeight: 500 }}>{dimension.name}</span>
          <span style={{ fontSize: 13, color: "#888" }}>{value}/5</span>
        </div>
        <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>
          {dimension.description}
        </div>
        <div>
          {[1, 2, 3, 4, 5].map((star) => (
            <Button
              key={star}
              type="text"
              icon={
                <StarFilled
                  style={{
                    color: star <= value ? "#fadb14" : "#d9d9d9",
                    fontSize: 22,
                    transition: "color 0.2s",
                  }}
                />
              }
              onClick={() => onChange(star)}
              style={{ padding: 0, marginRight: 2 }}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
        {/* 头部信息 */}
        <Card style={{ marginBottom: 24 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <Button
                type="text"
                size="small"
                onClick={() => navigate("/data/evaluation")}
                icon={<LeftOutlined />}
              >
                返回列表
              </Button>
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  {currentEvaluationTask?.name}
                </Title>
                <div style={{ color: "#888" }}>人工评估任务</div>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 13, color: "#888" }}>进度</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#1677ff" }}>
                {Math.round(progress)}%
              </div>
            </div>
          </div>

          {/* 任务基本信息 */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 16,
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <DatabaseOutlined style={{ color: "#888" }} />
              <span style={{ color: "#888" }}>数据集:</span>
              <span style={{ fontWeight: 500 }}>
                {currentEvaluationTask?.datasetName}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <ScissorOutlined style={{ color: "#888" }} />
              <span style={{ color: "#888" }}>切片方法:</span>
              <span style={{ fontWeight: 500 }}>
                {currentEvaluationTask?.sliceConfig?.method}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <AimOutlined style={{ color: "#888" }} />
              <span style={{ color: "#888" }}>样本数量:</span>
              <span style={{ fontWeight: 500 }}>{evaluationSlices.length}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <CalendarOutlined style={{ color: "#888" }} />
              <span style={{ color: "#888" }}>创建时间:</span>
              <span style={{ fontWeight: 500 }}>
                {currentEvaluationTask?.createdAt}
              </span>
            </div>
          </div>

          {/* 进度条 */}
          <div style={{ marginTop: 24 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 13,
                color: "#888",
                marginBottom: 6,
              }}
            >
              <span>
                当前进度: {currentSliceIndex + 1} / {evaluationSlices.length}
              </span>
              <span>{Math.round(progress)}% 完成</span>
            </div>
            <div
              style={{
                width: "100%",
                background: "#e5e7eb",
                borderRadius: 4,
                height: 8,
              }}
            >
              <div
                style={{
                  background: "#1677ff",
                  height: 8,
                  borderRadius: 4,
                  width: `${progress}%`,
                  transition: "width 0.3s",
                }}
              />
            </div>
          </div>
        </Card>

        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}
        >
          {/* 左侧：切片内容 */}
          <Card>
            <div
              style={{
                borderBottom: "1px solid #f0f0f0",
                paddingBottom: 16,
                marginBottom: 16,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span
                style={{
                  fontSize: 16,
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <FileTextOutlined />
                切片内容
              </span>
              <Badge
                count={`切片 ${currentSliceIndex + 1}`}
                style={{ background: "#fafafa", color: "#333" }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {currentSlice && (
                <>
                  {/* 切片元信息 */}
                  <div
                    style={{
                      background: "#fafafa",
                      borderRadius: 8,
                      padding: 16,
                      fontSize: 13,
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: 12,
                      }}
                    >
                      <div>
                        <span style={{ color: "#888" }}>来源文件:</span>
                        <span style={{ marginLeft: 6, fontWeight: 500 }}>
                          {currentSlice.sourceFile}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: "#888" }}>处理方法:</span>
                        <span style={{ marginLeft: 6, fontWeight: 500 }}>
                          {currentSlice.metadata.processingMethod}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: "#888" }}>位置:</span>
                        <span style={{ marginLeft: 6, fontWeight: 500 }}>
                          {currentSlice.metadata.startPosition}-
                          {currentSlice.metadata.endPosition}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: "#888" }}>章节:</span>
                        <span style={{ marginLeft: 6, fontWeight: 500 }}>
                          {currentSlice.metadata.section}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 切片内容 */}
                  <div
                    style={{
                      border: "1px solid #f0f0f0",
                      borderRadius: 8,
                      padding: 16,
                      minHeight: 180,
                    }}
                  >
                    <div
                      style={{ fontSize: 13, color: "#888", marginBottom: 8 }}
                    >
                      内容预览
                    </div>
                    <div style={{ color: "#222", lineHeight: 1.7 }}>
                      {currentSlice.content}
                    </div>
                  </div>

                  {/* 导航按钮 */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      borderTop: "1px solid #f0f0f0",
                      paddingTop: 16,
                      marginTop: 8,
                    }}
                  >
                    <Button
                      type="default"
                      icon={<LeftOutlined />}
                      onClick={() =>
                        setCurrentSliceIndex(Math.max(0, currentSliceIndex - 1))
                      }
                      disabled={currentSliceIndex === 0}
                    >
                      上一个
                    </Button>
                    <span style={{ fontSize: 13, color: "#888" }}>
                      {currentSliceIndex + 1} / {evaluationSlices.length}
                    </span>
                    <Button
                      type="default"
                      icon={<RightOutlined />}
                      onClick={() =>
                        setCurrentSliceIndex(
                          Math.min(
                            evaluationSlices.length - 1,
                            currentSliceIndex + 1
                          )
                        )
                      }
                      disabled={
                        currentSliceIndex === evaluationSlices.length - 1
                      }
                    >
                      下一个
                    </Button>
                  </div>
                </>
              )}
            </div>
          </Card>

          {/* 右侧：评估维度 */}
          <Card>
            <div
              style={{
                borderBottom: "1px solid #f0f0f0",
                paddingBottom: 16,
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  fontSize: 16,
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <StarFilled style={{ color: "#fadb14" }} />
                评估维度
              </span>
              <div style={{ fontSize: 13, color: "#888", marginTop: 4 }}>
                请为每个维度进行1-5星评分
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {allDimensions.map((dimension) => (
                <div
                  key={dimension.id}
                  style={{
                    border: "1px solid #f0f0f0",
                    borderRadius: 8,
                    padding: 16,
                  }}
                >
                  <StarRating
                    value={currentScores[dimension.id] || 0}
                    onChange={(score) =>
                      updateSliceScore(
                        currentSlice?.id || "",
                        dimension.id,
                        score
                      )
                    }
                    dimension={dimension}
                  />
                </div>
              ))}

              {/* 评论区域 */}
              <div
                style={{
                  border: "1px solid #f0f0f0",
                  borderRadius: 8,
                  padding: 16,
                }}
              >
                <span
                  style={{ fontWeight: 500, marginBottom: 8, display: "block" }}
                >
                  评估备注
                </span>
                <TextArea
                  placeholder="请输入对该切片的评估备注和建议..."
                  value={sliceComments[currentSlice?.id || ""] || ""}
                  onChange={(e) =>
                    setSliceComments((prev) => ({
                      ...prev,
                      [currentSlice?.id || ""]: e.target.value,
                    }))
                  }
                  rows={3}
                />
              </div>

              {/* 保存按钮 */}
              <div style={{ borderTop: "1px solid #f0f0f0", paddingTop: 16 }}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSaveAndNext}
                  block
                  size="large"
                >
                  {currentSliceIndex === evaluationSlices.length - 1
                    ? "完成评估"
                    : "保存并下一个"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ManualEvaluatePage;
