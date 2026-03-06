import React from 'react';

export interface ImagePreviewProps {
  blobUrl?: string;
  alt?: string;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  blobUrl,
  alt = 'Preview'
}) => {
  if (!blobUrl) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No image available
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-full bg-gray-50">
      <img
        src={blobUrl}
        alt={alt}
        className="max-w-full max-h-[600px] object-contain"
      />
    </div>
  );
};
