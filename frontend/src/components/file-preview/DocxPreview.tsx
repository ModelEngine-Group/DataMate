import React, { useEffect, useState } from 'react';
import mammoth from 'mammoth';

export interface DocxPreviewProps {
  blob?: Blob;
  fileName?: string;
}

export const DocxPreview: React.FC<DocxPreviewProps> = ({
  blob,
  fileName
}) => {
  const [html, setHtml] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!blob) {
      setError('No file content');
      setLoading(false);
      return;
    }

    const convertDocx = async () => {
      try {
        setLoading(true);
        setError('');

        const arrayBuffer = await blob.arrayBuffer();
        const result = await mammoth.convertToHtml({ arrayBuffer });
        setHtml(result.value);
      } catch (err) {
        setError('Failed to convert Word document');
      } finally {
        setLoading(false);
      }
    };

    convertDocx();
  }, [blob]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span>Converting document...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        <div className="text-center">
          <p className="mb-2">⚠️ {error}</p>
          <p className="text-sm text-gray-400">Please download the file to view</p>
        </div>
      </div>
    );
  }

  if (!html) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6 bg-white">
      <div
        className="docx-content prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
};
