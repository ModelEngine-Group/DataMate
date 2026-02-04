import { useState, useEffect } from "react";
import { Button, Card, Badge, Input, Typography, Breadcrumb } from "antd";
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
import DetailHeader from "@/components/DetailHeader";
import { useTranslation } from "react-i18next";

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

const ManualEvaluatePage = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const taskId = mockTasks[0].id;
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
      window.alert(t("dataEvaluation.evaluate.scoreAllDimensions"));
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

  // 头部统计信息
  const statistics = [
    {
      icon: <DatabaseOutlined className="text-gray-500" />,
      label: t("dataEvaluation.evaluate.stats.dataset"),
      value: currentEvaluationTask?.datasetName || "",
    },
    {
      icon: <ScissorOutlined className="text-gray-500" />,
      label: t("dataEvaluation.evaluate.stats.sliceMethod"),
      value: currentEvaluationTask?.sliceConfig?.method || "",
    },
    {
      icon: <AimOutlined className="text-gray-500" />,
      label: t("dataEvaluation.evaluate.stats.sampleCount"),
      value: evaluationSlices.length,
    },
    {
      icon: <CalendarOutlined className="text-gray-500" />,
      label: t("dataEvaluation.evaluate.stats.createdAt"),
      value: currentEvaluationTask?.createdAt || "",
    },
  ];

  return (
    <div className="space-y-4">
      <Breadcrumb
        items={[
          {
            title: (
              <span onClick={() => navigate("/data/evaluation")}>
                {t("dataEvaluation.detail.breadcrumb.home")}
              </span>
            ),
          },
          { title: t("dataEvaluation.evaluate.breadcrumb.manual"), key: "manual-evaluate" },
        ]}
      />
      {/* 头部信息 */}
      <DetailHeader
        data={{
          name: currentEvaluationTask?.name || "",
          description: t("dataEvaluation.evaluate.manualTaskDesc"),
          icon: <FileTextOutlined />,
          createdAt: currentEvaluationTask?.createdAt,
          lastUpdated: currentEvaluationTask?.createdAt,
        }}
        statistics={statistics}
        operations={[]}
      />
      {/* 进度条 */}
      <div className="flex justify-between items-center mt-4 mb-6">
        <div className="text-xs text-gray-500">
          {t("dataEvaluation.evaluate.progress.current", {
            current: currentSliceIndex + 1,
            total: evaluationSlices.length,
          })}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500">
            {t("dataEvaluation.evaluate.progress.complete", {
              percent: Math.round(progress),
            })}
          </span>
          <div className="w-48 bg-gray-200 rounded h-2">
            <div
              className="bg-blue-600 h-2 rounded transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-2xl font-bold text-blue-600">
            {Math.round(progress)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {/* 左侧：切片内容 */}
        <Card>
          <div className="border-b border-gray-100 pb-4 mb-4 flex justify-between items-center">
            <span className="text-base font-semibold flex items-center gap-2">
              <FileTextOutlined />
              {t("dataEvaluation.evaluate.sliceContent")}
            </span>
            <Badge
              count={t("dataEvaluation.evaluate.sliceLabel", {
                index: currentSliceIndex + 1,
              })}
              style={{ background: "#fafafa", color: "#333" }}
            />
          </div>

          <div className="flex flex-col gap-2">
            {currentSlice && (
              <>
                {/* 切片元信息 */}
                <div className="bg-gray-50 rounded p-4 text-sm">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="text-gray-500">
                        {t("dataEvaluation.evaluate.sourceFile")}
                      </span>
                      <span className="ml-2 font-medium">
                        {currentSlice.sourceFile}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">
                        {t("dataEvaluation.evaluate.processingMethod")}
                      </span>
                      <span className="ml-2 font-medium">
                        {currentSlice.metadata.processingMethod}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">
                        {t("dataEvaluation.evaluate.position")}
                      </span>
                      <span className="ml-2 font-medium">
                        {currentSlice.metadata.startPosition}-
                        {currentSlice.metadata.endPosition}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">
                        {t("dataEvaluation.evaluate.section")}
                      </span>
                      <span className="ml-2 font-medium">
                        {currentSlice.metadata.section}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 切片内容 */}
                <div className="border border-gray-100 rounded p-4 min-h-[180px]">
                  <div className="text-xs text-gray-500 mb-2">
                    {t("dataEvaluation.evaluate.contentPreview")}
                  </div>
                  <div className="text-gray-900 leading-relaxed">
                    {currentSlice.content}
                  </div>
                </div>

                {/* 导航按钮 */}
                <div className="flex items-center justify-between border-t border-gray-100 pt-4 mt-2">
                  <Button
                    type="default"
                    icon={<LeftOutlined />}
                    onClick={() =>
                      setCurrentSliceIndex(Math.max(0, currentSliceIndex - 1))
                    }
                    disabled={currentSliceIndex === 0}
                  >
                    {t("dataEvaluation.evaluate.prev")}
                  </Button>
                  <span className="text-xs text-gray-500">
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
                    disabled={currentSliceIndex === evaluationSlices.length - 1}
                  >
                    {t("dataEvaluation.evaluate.next")}
                  </Button>
                </div>
              </>
            )}
          </div>
        </Card>

        {/* 右侧：评估维度 */}
        <Card>
          <div className="border-b border-gray-100 pb-4 mb-4">
            <span className="text-base font-semibold flex items-center gap-2">
              <StarFilled className="text-yellow-400" />
              {t("dataEvaluation.evaluate.dimensions")}
            </span>
            <div className="text-xs text-gray-500 mt-1">
              {t("dataEvaluation.evaluate.dimensionsHint")}
            </div>
          </div>

          <div className="flex flex-col gap-4">
            {allDimensions.map((dimension) => (
              <div
                key={dimension.id}
                className="border border-gray-100 rounded p-4"
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
            <div className="border border-gray-100 rounded p-4">
              <span className="font-medium mb-2 block">
                {t("dataEvaluation.evaluate.evaluationNote")}
              </span>
              <TextArea
                placeholder={t("dataEvaluation.evaluate.notePlaceholder")}
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
            <div className="border-t border-gray-100 pt-4">
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSaveAndNext}
                block
                size="large"
              >
                {currentSliceIndex === evaluationSlices.length - 1
                  ? t("dataEvaluation.evaluate.completeEval")
                  : t("dataEvaluation.evaluate.saveAndNext")}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ManualEvaluatePage;
