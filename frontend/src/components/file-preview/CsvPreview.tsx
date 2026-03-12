import React, { useMemo } from 'react';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export interface CsvPreviewProps {
  content?: string;
  fileName?: string;
}

interface DataType {
  key: number;
  [key: string]: string;
}

export const CsvPreview: React.FC<CsvPreviewProps> = ({
  content = '',
  fileName
}) => {
  // 解析 CSV
  const { headers, rows, error } = useMemo(() => {
    if (!content) {
      return { headers: [], rows: [], error: 'No content available' };
    }

    try {
      const lines = content.split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        return { headers: [], rows: [], error: 'Empty file' };
      }

      // 解析 CSV 处理引号
      const parseCSVLine = (line: string): string[] => {
        const result: string[] = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
          const char = line[i];
          const nextChar = line[i + 1];

          if (char === '"') {
            if (inQuotes && nextChar === '"') {
              // 转义的引号
              current += '"';
              i++; // 跳过下一个引号
            } else {
              inQuotes = !inQuotes;
            }
          } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
          } else {
            current += char;
          }
        }

        result.push(current);
        return result.map(cell => cell.trim());
      };

      const headers = parseCSVLine(lines[0]);
      const dataRows = lines.slice(1).map((line, idx) => {
        const values = parseCSVLine(line);
        const row: DataType = {
          key: idx,
        };
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        return row;
      });

      return { headers, rows: dataRows, error: null };
    } catch (err) {
      return {
        headers: [],
        rows: [],
        error: err instanceof Error ? err.message : 'Failed to parse CSV'
      };
    }
  }, [content]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        <div className="text-center">
          <p className="text-lg mb-2">⚠️ CSV Parse Failed</p>
          <p className="text-sm text-gray-400 mb-4">{error}</p>
          <p className="text-xs text-gray-500">Displaying as plain text</p>
        </div>
      </div>
    );
  }

  if (headers.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  // 动态生成列定义
  const columns: ColumnsType<DataType> = headers.map(header => ({
    title: header,
    dataIndex: header,
    key: header,
    width: 150,
    ellipsis: true,
    render: (text: string) => text || '-'
  }));

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 文件信息 */}
      {fileName && (
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
          <span className="text-sm text-gray-600">
            📄 {fileName} ({rows.length} rows × {headers.length} columns)
          </span>
        </div>
      )}

      {/* 表格 */}
      <div className="flex-1 overflow-auto">
        <Table
          columns={columns}
          dataSource={rows}
          pagination={false}
          size="small"
          bordered
          scroll={{ x: 'max-content', y: 'calc(100vh - 200px)' }}
          rowKey={(record) => record.key}
        />
      </div>
    </div>
  );
};
