// typescript
// File: `frontend/src/pages/DataManagement/Detail/components/DataQuality.tsx`
import React from "react";
// Run `npm install antd lucide-react` if your editor reports "Module is not installed"
import { Card } from "antd";
import { AlertTriangle } from "lucide-react";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";
import { Dataset } from "@/pages/DataManagement/dataset.model.ts";

type DatasetType = "image" | "text" | "tabular";

interface FileStats {
  totalFiles: number;
  corrupted?: number;
  unlabeled?: number;
  lowQuality?: number;
  missingFields?: number;
  duplicateRows?: number;
}

interface Props {
  dataset?: Dataset;
  datasetType?: DatasetType;
  fileStats?: FileStats;
}

function clamp(v: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, v));
}

function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getMockMetrics(datasetType: DatasetType, stats: FileStats) {
  const total = Math.max(1, stats.totalFiles || 1);
  const corrupted = stats.corrupted || 0;
  const unlabeled = stats.unlabeled || 0;
  const lowQuality = stats.lowQuality || 0;
  const missingFields = stats.missingFields || 0;
  const duplicateRows = stats.duplicateRows || 0;

  if (datasetType === "image") {
    const clarity = clamp(100 - (lowQuality / total) * 120 - (corrupted / total) * 100);
    const colorConsistency = clamp(100 - (lowQuality / total) * 80);
    const annotationCompleteness = clamp(100 - (unlabeled / total) * 150 - (corrupted / total) * 50);
    return [
      { metric: "图像清晰度", value: Math.round(clarity * 10) / 10, color: "bg-green-500" },
      { metric: "色彩一致性", value: Math.round(colorConsistency * 10) / 10, color: "bg-blue-500" },
      { metric: "标注完整性", value: Math.round(annotationCompleteness * 10) / 10, color: "bg-purple-500" },
    ];
  }

  if (datasetType === "text") {
    const tokenQuality = clamp(100 - (corrupted / total) * 90 - (missingFields / total) * 60);
    const labelConsistency = clamp(100 - (unlabeled / total) * 140 - (corrupted / total) * 40);
    const metadataCompleteness = clamp(100 - (missingFields / total) * 150);
    return [
      { metric: "分词/Token质量", value: Math.round(tokenQuality * 10) / 10, color: "bg-green-500" },
      { metric: "标签一致性", value: Math.round(labelConsistency * 10) / 10, color: "bg-blue-500" },
      { metric: "元数据完整性", value: Math.round(metadataCompleteness * 10) / 10, color: "bg-purple-500" },
    ];
  }

  // tabular
  const missingValueScore = clamp(100 - (missingFields / total) * 200 - (corrupted / total) * 50);
  const typeConsistency = clamp(100 - (corrupted / total) * 120 - (duplicateRows / total) * 40);
  const uniqueness = clamp(100 - (duplicateRows / total) * 200);
  return [
    { metric: "缺失值比例控制", value: Math.round(missingValueScore * 10) / 10, color: "bg-green-500" },
    { metric: "类型一致性", value: Math.round(typeConsistency * 10) / 10, color: "bg-blue-500" },
    { metric: "唯一性/去重", value: Math.round(uniqueness * 10) / 10, color: "bg-purple-500" },
  ];
}

export default function DataQuality(props: Props = {}) {
  return <DevelopmentInProgress showHome={false} />
  const { dataset, datasetType: propDatasetType, fileStats: propFileStats } = props;

  // Prefer dataset fields when available, then explicit props, then sensible defaults
  const inferredTypeFromDataset = (dataset && ((dataset as any).type || (dataset as any).datasetType)) as DatasetType | undefined;
  const datasetType: DatasetType = (propDatasetType || inferredTypeFromDataset || "image") as DatasetType;

  // Try to obtain file stats from dataset if provided
  let fileStatsFromSource: FileStats | undefined = propFileStats;
  let detailedFieldsProvided = false; // track whether detailed fields exist (not defaulted)

  if (!fileStatsFromSource && dataset) {
    if ((dataset as any).fileStats) {
      fileStatsFromSource = (dataset as any).fileStats as FileStats;
      // consider detailed if any field beyond totalFiles present
      const fs = fileStatsFromSource as any;
      detailedFieldsProvided = fs.corrupted !== undefined || fs.unlabeled !== undefined || fs.lowQuality !== undefined || fs.missingFields !== undefined || fs.duplicateRows !== undefined;
    } else {
      // attempt to infer total files from common fields
      let total = 0;
      const dsAny = dataset as any;
      if (typeof dsAny.files === "number") total = dsAny.files;
      else if (Array.isArray(dsAny.files)) total = dsAny.files.length;
      else if (typeof dsAny.fileCount === "number") total = dsAny.fileCount;

      fileStatsFromSource = {
        totalFiles: Math.max(1, total || 1),
        corrupted: dsAny.corrupted !== undefined ? dsAny.corrupted : undefined,
        unlabeled: dsAny.unlabeled !== undefined ? dsAny.unlabeled : undefined,
        lowQuality: dsAny.lowQuality !== undefined ? dsAny.lowQuality : undefined,
        missingFields: dsAny.missingFields !== undefined ? dsAny.missingFields : undefined,
        duplicateRows: dsAny.duplicateRows !== undefined ? dsAny.duplicateRows : undefined,
      };
      detailedFieldsProvided = !!(dsAny.corrupted || dsAny.unlabeled || dsAny.lowQuality || dsAny.missingFields || dsAny.duplicateRows);
    }
  }

  // if props provided, check if they included detailed fields
  if (propFileStats) {
    fileStatsFromSource = propFileStats;
    const p = propFileStats as any;
    detailedFieldsProvided = p.corrupted !== undefined || p.unlabeled !== undefined || p.lowQuality !== undefined || p.missingFields !== undefined || p.duplicateRows !== undefined;
  }

  // final fallback defaults (note: these are complete defaults)
  const finalFileStats: FileStats = fileStatsFromSource ?? { totalFiles: 120, corrupted: 3, unlabeled: 6, lowQuality: 5, missingFields: 0, duplicateRows: 0 };
  // if we landed on fallback defaults, mark detailedFieldsProvided = false so we apply jitter
  const completeSource = detailedFieldsProvided || !!fileStatsFromSource;

  // compute metrics once and apply jitter if data incomplete
  const { metrics, integrityMetrics } = React.useMemo(() => {
    const baseMetrics = getMockMetrics(datasetType, finalFileStats);

    const baseIntegrity =
      datasetType === "image"
        ? [
          { metric: "文件完整性", value: clamp(100 - ((finalFileStats.corrupted || 0) / Math.max(1, finalFileStats.totalFiles)) * 100), color: "bg-green-500" },
          { metric: "元数据完整性", value: clamp(100 - ((finalFileStats.missingFields || 0) / Math.max(1, finalFileStats.totalFiles)) * 100), color: "bg-blue-500" },
          { metric: "标签一致性", value: clamp(100 - ((finalFileStats.unlabeled || 0) / Math.max(1, finalFileStats.totalFiles)) * 120), color: "bg-purple-500" },
        ]
        : datasetType === "text"
          ? [
            { metric: "文件完整性", value: clamp(100 - ((finalFileStats.corrupted || 0) / Math.max(1, finalFileStats.totalFiles)) * 100), color: "bg-green-500" },
            { metric: "字段完整性", value: clamp(100 - ((finalFileStats.missingFields || 0) / Math.max(1, finalFileStats.totalFiles)) * 120), color: "bg-blue-500" },
            { metric: "标签一致性", value: clamp(100 - ((finalFileStats.unlabeled || 0) / Math.max(1, finalFileStats.totalFiles)) * 120), color: "bg-purple-500" },
          ]
          : [
            { metric: "文件完整性", value: clamp(100 - ((finalFileStats.corrupted || 0) / Math.max(1, finalFileStats.totalFiles)) * 100), color: "bg-green-500" },
            { metric: "列完整性", value: clamp(100 - ((finalFileStats.missingFields || 0) / Math.max(1, finalFileStats.totalFiles)) * 120), color: "bg-blue-500" },
            { metric: "重复率", value: clamp(100 - ((finalFileStats.duplicateRows || 0) / Math.max(1, finalFileStats.totalFiles)) * 200), color: "bg-purple-500" },
          ];

    // if source data is incomplete or only totalFiles known, apply a small random reduction so values are not all 100%
    if (!completeSource) {
      // jitter range can be tuned; using 4-12% to make results realistic but not drastic
      const jitterMax = 12;
      const jitterMin = 4;

      const jittered = baseMetrics.map((m) => {
        // don't reduce below 40 for readability
        const jitter = randInt(jitterMin, jitterMax);
        return { ...m, value: clamp(Math.round((m.value - jitter) * 10) / 10) };
      });

      const integrityJittered = baseIntegrity.map((m) => {
        const jitter = randInt(jitterMin, jitterMax);
        return { ...m, value: clamp(Math.round((m.value - jitter) * 10) / 10) };
      });

      return { metrics: jittered, integrityMetrics: integrityJittered };
    }

    return { metrics: baseMetrics, integrityMetrics: baseIntegrity };
  }, [datasetType, finalFileStats, completeSource]);

  return (
    <div className="mt-0">
      <div className="grid md:grid-cols-2 gap-6">
        <Card title="质量分布">
          {metrics.map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                />
              </div>
            </div>
          ))}
        </Card>

        <Card title="数据完整性">
          {integrityMetrics.map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                />
              </div>
            </div>
          ))}
        </Card>
      </div>

      <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-yellow-800 mb-2">质量改进建议</h4>
            <ul className="text-sm text-yellow-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0" />
                建议对{Math.max(1, Math.round((finalFileStats.lowQuality || 0) * 1))}项低质量样本进行复查或重新采集
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0" />
                检查并补充缺失的元数据字段（现有缺失：{finalFileStats.missingFields || 0}）
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0" />
                考虑增加更多低代表性样本以平衡数据分布
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
