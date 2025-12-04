import { useEffect, useState } from 'react';
import { Table, Typography, Button, Space, Empty, Tooltip } from 'antd';
import { FolderOpen, FileText, ArrowLeft } from 'lucide-react';
import { queryEvaluationFilesUsingGet, queryEvaluationItemsUsingGet } from '../../evaluation.api';
import useFetchData from '@/hooks/useFetchData';

const { Text } = Typography;

const COLUMN_WIDTH = 520;
 const MONO_FONT = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
 const codeBlockStyle = {
   fontFamily: MONO_FONT,
   fontSize: 12,
   lineHeight: '20px',
   color: '#334155',
   backgroundColor: '#f8fafc',
   border: '1px solid #f0f0f0',
   borderRadius: 6,
   padding: 8,
 } as const;

type EvalFile = {
  taskId: string;
  fileId: string;
  fileName: string;
  totalCount: number;
  evaluatedCount: number;
  pendingCount: number;
};

type EvalItem = {
  id: string;
  taskId: string;
  itemId: string;
  fileId: string;
  evalContent: any;
  evalScore?: number | null;
  evalResult: any;
  status?: string;
};

export default function EvaluationItems({ task }: { task: any }) {
  const [selectedFile, setSelectedFile] = useState<{ fileId: string; fileName: string } | null>(null);

  // 文件列表数据（使用 useFetchData），pageOffset=0 表示后端分页为 1 基
  const {
    loading: loadingFiles,
    tableData: files,
    pagination: filePagination,
    setSearchParams: setFileSearchParams,
  } = useFetchData<EvalFile>(
    (params) => queryEvaluationFilesUsingGet({ taskId: task?.id, ...params }),
    (d) => d as unknown as EvalFile,
    30000,
    false,
    [],
    0
  );

  // 评估条目数据（使用 useFetchData），依赖选中文件
  const {
    loading: loadingItems,
    tableData: items,
    pagination: itemPagination,
    setSearchParams: setItemSearchParams,
    fetchData: fetchItems,
  } = useFetchData<EvalItem>(
    (params) => {
      if (!task?.id || !selectedFile?.fileId) {
        return Promise.resolve({ data: { content: [], totalElements: 0 } });
      }
      return queryEvaluationItemsUsingGet({ taskId: task.id, file_id: selectedFile.fileId, ...params });
    },
    (d) => d as unknown as EvalItem,
    30000,
    false,
    [],
    0
  );

  // 当选择文件变化时，主动触发一次条目查询，避免仅依赖 searchParams 变更导致未触发
  useEffect(() => {
    if (task?.id && selectedFile?.fileId) {
      setItemSearchParams((prev: any) => ({ ...prev, current: 1 }));
      // 立即拉取一次，保证点击后立刻出现数据
      fetchItems();
    }
  }, [task?.id, selectedFile?.fileId]);

  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'fileName',
      key: 'fileName',
      render: (_: any, record: EvalFile) => (
        <Space onClick={(e) => { e.stopPropagation(); setSelectedFile({ fileId: record.fileId, fileName: record.fileName }); }} style={{ cursor: 'pointer' }}>
          <FolderOpen size={16} />
          <Button type="link" style={{ padding: 0 }}>{record.fileName}</Button>
        </Space>
      ),
    },
    {
      title: '总条目',
      dataIndex: 'totalCount',
      key: 'totalCount',
      width: 120,
    },
    {
      title: '已评估',
      dataIndex: 'evaluatedCount',
      key: 'evaluatedCount',
      width: 120,
    },
    {
      title: '待评估',
      dataIndex: 'pendingCount',
      key: 'pendingCount',
      width: 120,
    },
  ];

  const renderEvalObject = (rec: EvalItem) => {
    const c = rec.evalContent;
    let jsonString = '';
    try {
      if (typeof c === 'string') {
        // 尝试将字符串解析为 JSON，失败则按原字符串显示
        try {
          jsonString = JSON.stringify(JSON.parse(c), null, 2);
        } catch {
          jsonString = JSON.stringify({ value: c }, null, 2);
        }
      } else {
        jsonString = JSON.stringify(c, null, 2);
      }
    } catch {
      jsonString = 'null';
    }
    return (
      <Tooltip
        color="#fff"
        title={<pre style={{ ...codeBlockStyle, margin: 0, maxWidth: COLUMN_WIDTH, whiteSpace: 'pre-wrap' }}>{jsonString}</pre>}
        overlayInnerStyle={{ maxHeight: 600, overflow: 'auto', width: COLUMN_WIDTH }}
      >
        <Typography.Paragraph
          style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: MONO_FONT, fontSize: 12, lineHeight: '20px', color: '#334155' }}
          ellipsis={{ rows: 6 }}
        >
          <pre style={{ ...codeBlockStyle, whiteSpace: 'pre-wrap', margin: 0 }}>{jsonString}</pre>
        </Typography.Paragraph>
      </Tooltip>
    );
  };

  const renderEvalResult = (rec: EvalItem) => {
    const r = rec.evalResult;
    let jsonString = '';
    try {
      if (typeof r === 'string') {
        try {
          jsonString = JSON.stringify(JSON.parse(r), null, 2);
        } catch {
          jsonString = JSON.stringify({ value: r, score: rec.evalScore ?? undefined }, null, 2);
        }
      } else {
        const withScore = rec.evalScore !== undefined && rec.evalScore !== null ? { ...r, evalScore: rec.evalScore } : r;
        jsonString = JSON.stringify(withScore, null, 2);
      }
    } catch {
      jsonString = 'null';
    }
    // 判空展示未评估
    const isEmpty = !r || (typeof r === 'string' && r.trim() === '') || (typeof r === 'object' && r !== null && Object.keys(r).length === 0);
    if (isEmpty) {
      return <Text type="secondary">未评估</Text>;
    }
    return (
      <Tooltip
        color="#fff"
        title={<pre style={{ ...codeBlockStyle, margin: 0, maxWidth: 800, whiteSpace: 'pre-wrap' }}>{jsonString}</pre>}
        overlayInnerStyle={{ maxHeight: 600, overflow: 'auto' }}
      >
        <Typography.Paragraph
          style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: MONO_FONT, fontSize: 12, lineHeight: '20px', color: '#334155' }}
          ellipsis={{ rows: 6 }}
        >
          <pre style={{ ...codeBlockStyle, whiteSpace: 'pre-wrap', margin: 0 }}>{jsonString}</pre>
        </Typography.Paragraph>
      </Tooltip>
    );
  };

  const itemColumns = [
    {
      title: '评估对象',
      dataIndex: 'evalContent',
      key: 'evalContent',
      render: (_: any, record: EvalItem) => renderEvalObject(record),
      width: COLUMN_WIDTH,
    },
    {
      title: '评估结果',
      dataIndex: 'evalResult',
      key: 'evalResult',
      render: (_: any, record: EvalItem) => renderEvalResult(record),
      width: COLUMN_WIDTH,
    },
  ];

  if (!task?.id) return <Empty description="任务不存在" />;

  return (
    <div className="flex flex-col gap-4">
      {!selectedFile ? (
        <Table
          rowKey={(r: EvalFile) => r.fileId}
          columns={fileColumns}
          dataSource={files}
          loading={loadingFiles}
          size="middle"
          onRow={(record) => ({
            onClick: () => {
              setSelectedFile({ fileId: record.fileId, fileName: record.fileName });
              // 切换文件时，重置条目表到第一页
              setItemSearchParams((prev: any) => ({ ...prev, current: 1 }));
            },
          })}
          pagination={filePagination}
        />
      ) : (
        <div className="flex flex-col gap-3">
          <div className="sticky top-0 z-10 bg-white py-2" style={{ borderBottom: '1px solid #f0f0f0' }}>
            <Space wrap>
              <Button icon={<ArrowLeft size={16} />} onClick={() => { setSelectedFile(null); }}>
                返回文件列表
              </Button>
              <Space>
                <FileText size={16} />
                <Text strong>{selectedFile.fileName}</Text>
                <Text type="secondary">文件ID：{selectedFile.fileId}</Text>
                <Text type="secondary">共 {itemPagination.total} 条</Text>
              </Space>
            </Space>
          </div>
          <Table
            rowKey={(r: EvalItem) => r.id}
            columns={itemColumns}
            dataSource={items}
            loading={loadingItems}
            size="middle"
            pagination={itemPagination}
          />
        </div>
      )}
    </div>
  );
}
