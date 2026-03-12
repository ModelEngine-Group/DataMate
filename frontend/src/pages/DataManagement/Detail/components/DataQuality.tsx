import React, { useMemo } from "react";
import { Card, Table, Progress, Empty } from "antd";
import { Tags, BarChart3 } from "lucide-react";
import { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import { useTranslation } from "react-i18next";

// 数据集标签分布统计组件
interface LabelDistributionProps {
  distribution?: Record<string, Record<string, number>>;
}

function LabelDistributionStats({ distribution }: LabelDistributionProps) {
  const { t } = useTranslation();

  // 将 distribution 数据转换为表格格式
  const { tableData, totalLabels } = useMemo(() => {
    if (!distribution) return { tableData: [], totalLabels: 0 };

    const data: Array<{
      category: string;
      label: string;
      count: number;
      percentage: number;
    }> = [];

    let total = 0;

    // 遍历 distribution 对象
    Object.entries(distribution).forEach(([category, labels]) => {
      if (typeof labels === 'object' && labels !== null) {
        Object.entries(labels).forEach(([label, count]) => {
          const numCount = typeof count === 'number' ? count : 0;
          total += numCount;
          data.push({
            category,
            label,
            count: numCount,
            percentage: 0, // 稍后计算
          });
        });
      }
    });

    // 计算百分比
    data.forEach(item => {
      item.percentage = total > 0 ? (item.count / total) * 100 : 0;
    });

    // 按 count 降序排序
    data.sort((a, b) => b.count - a.count);

    return { tableData: data, totalLabels: total };
  }, [distribution]);

  const columns = [
    {
      title: t("dataManagement.quality.labelDistribution.category"),
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (text: string) => (
        <span className="font-medium text-gray-700">{text || t("dataManagement.quality.labelDistribution.uncategorized")}</span>
      ),
    },
    {
      title: t("dataManagement.quality.labelDistribution.labelName"),
      dataIndex: 'label',
      key: 'label',
      render: (text: string) => <span>{text}</span>,
    },
    {
      title: t("dataManagement.quality.labelDistribution.count"),
      dataIndex: 'count',
      key: 'count',
      width: 100,
      sorter: (a: any, b: any) => a.count - b.count,
      render: (count: number) => (
        <span className="font-semibold">{count}</span>
      ),
    },
    {
      title: t("dataManagement.quality.labelDistribution.percentage"),
      dataIndex: 'percentage',
      key: 'percentage',
      width: 200,
      sorter: (a: any, b: any) => a.percentage - b.percentage,
      render: (percentage: number) => (
        <div className="flex items-center gap-3">
          <Progress
            percent={parseFloat(percentage.toFixed(1))}
            size="small"
            showInfo={true}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>
      ),
    },
  ];

  // 按类别分组的视图数据
  const categoryGroups = useMemo(() => {
    if (!tableData.length) return {};

    return tableData.reduce((acc, item) => {
      if (!acc[item.category]) {
        acc[item.category] = [];
      }
      acc[item.category].push(item);
      return acc;
    }, {} as Record<string, typeof tableData>);
  }, [tableData]);

  if (!distribution || Object.keys(distribution).length === 0) {
    return (
      <Card className="bg-gray-50">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={t("dataManagement.quality.labelDistribution.noData")}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* 表格视图 */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            <span>{t("dataManagement.quality.labelDistribution.title")}</span>
          </div>
        }
      >
        <Table
          columns={columns}
          dataSource={tableData}
          rowKey={(record) => `${record.category}-${record.label}`}
          pagination={{
            pageSize: 10,
            showTotal: (total) => t("dataManagement.quality.labelDistribution.paginationTotal", { total }),
            showSizeChanger: true,
          }}
          size="small"
        />
      </Card>
    </div>
  );
}

export default function DataQuality({ dataset }: { dataset?: Dataset }) {
  return (
    <div className="mt-0">
      <LabelDistributionStats distribution={(dataset as any)?.distribution} />
    </div>
  );
}
