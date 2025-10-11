import { Dataset } from "../../dataset.model";

export default function DataLineageFlow(dataset: Dataset) {
  const lineage = dataset.lineage;
  if (!lineage) return null;

  const steps = [
    { name: "数据源", value: lineage.source, icon: Database },
    ...lineage.processing.map((step, index) => ({
      name: `处理${index + 1}`,
      value: step,
      icon: GitBranch,
    })),
  ];

  if (lineage.training) {
    steps.push({
      name: "模型训练",
      value: `${lineage.training.model} (准确率: ${lineage.training.accuracy}%)`,
      icon: Target,
    });
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        {steps.map((step, index) => (
          <div key={index} className="flex items-start gap-4 pb-8 last:pb-0">
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                <step.icon className="w-6 h-6 text-white" />
              </div>
              {index < steps.length - 1 && (
                <div className="w-0.5 h-12 bg-gradient-to-b from-blue-200 to-indigo-200 mt-2"></div>
              )}
            </div>
            <div className="flex-1 pt-3">
              <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                <h5 className="font-semibold text-gray-900 mb-1">
                  {step.name}
                </h5>
                <p className="text-sm text-gray-600">{step.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
