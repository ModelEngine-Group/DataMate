import { useEffect, useState } from 'react';
import { Table, Typography, Button, Space, Spin, Empty, message, Tooltip } from 'antd';
import { FolderOpen, FileText, ArrowLeft } from 'lucide-react';
import { queryEvaluationFilesUsingGet, queryEvaluationItemsUsingGet } from '../../evaluation.api';

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
  const [loadingFiles, setLoadingFiles] = useState<boolean>(false);
  const [files, setFiles] = useState<EvalFile[]>([]);
  const [filePagination, setFilePagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const [selectedFile, setSelectedFile] = useState<{ fileId: string; fileName: string } | null>(null);
  const [loadingItems, setLoadingItems] = useState<boolean>(false);
  const [items, setItems] = useState<EvalItem[]>([]);
  const [itemPagination, setItemPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // Fetch files list
  useEffect(() => {
    if (!task?.id || selectedFile) return;
    const fetchFiles = async () => {
      setLoadingFiles(true);
      try {
        const res = await queryEvaluationFilesUsingGet({ taskId: task.id, page: filePagination.current, size: filePagination.pageSize });
        const data = res?.data;
        const list: EvalFile[] = data?.content || [];
        setFiles(list);
        setFilePagination((p) => ({ ...p, total: data?.totalElements || 0 }));
      } catch (e) {
        message.error('加载评估文件失败');
        console.error(e);
      } finally {
        setLoadingFiles(false);
      }
    };
    fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task?.id, filePagination.current, filePagination.pageSize, selectedFile]);

  // Fetch items of selected file
  useEffect(() => {
    if (!task?.id || !selectedFile) return;
    const fetchItems = async () => {
      setLoadingItems(true);
      try {
        const res = await queryEvaluationItemsUsingGet({
          taskId: task.id,
          page: itemPagination.current,
          size: itemPagination.pageSize,
          file_id: selectedFile.fileId,
        });
        const data = res?.data;
        const list: EvalItem[] = data?.content || [];
        setItems(list);
        setItemPagination((p) => ({ ...p, total: data?.totalElements || 0 }));
      } catch (e) {
        message.error('加载评估条目失败');
        console.error(e);
      } finally {
        setLoadingItems(false);
      }
    };
    fetchItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task?.id, selectedFile?.fileId, itemPagination.current, itemPagination.pageSize]);

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
          onRow={(record) => ({ onClick: () => setSelectedFile({ fileId: record.fileId, fileName: record.fileName }) })}
          pagination={{
            current: filePagination.current,
            pageSize: filePagination.pageSize,
            total: filePagination.total,
            onChange: (current, pageSize) => setFilePagination({ current, pageSize, total: filePagination.total }),
          }}
        />
      ) : (
        <div className="flex flex-col gap-3">
          <div className="sticky top-0 z-10 bg-white py-2" style={{ borderBottom: '1px solid #f0f0f0' }}>
            <Space wrap>
              <Button icon={<ArrowLeft size={16} />} onClick={() => { setSelectedFile(null); setItems([]); }}>
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
            pagination={{
              current: itemPagination.current,
              pageSize: itemPagination.pageSize,
              total: itemPagination.total,
              onChange: (current, pageSize) => setItemPagination({ current, pageSize, total: itemPagination.total }),
            }}
          />
        </div>
      )}
    </div>
  );
}
