import { useState, useCallback } from 'react';
import { apiClient } from '../../services/api';
import type { FileAsset } from '../../types';

interface FileUploadProps {
  onUploadComplete: (file: FileAsset) => void;
  onError: (error: string) => void;
}

export default function FileUpload({ onUploadComplete, onError }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    console.log('[FileUpload] Handling file:', {
      name: file.name,
      type: file.type,
      size: file.size,
    });

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      console.error('[FileUpload] File too large:', file.size);
      onError('File size exceeds 10MB limit');
      return;
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/png',
      'image/jpeg',
    ];
    if (!allowedTypes.includes(file.type)) {
      console.error('[FileUpload] Invalid file type:', file.type);
      onError('File type not supported. Allowed: PDF, TXT, DOCX, PNG, JPEG');
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      // Get file extension
      const fileExtension = file.name.split('.').pop()?.toLowerCase() || '';
      const fileTypeMap: Record<string, string> = {
        pdf: 'pdf',
        txt: 'txt',
        docx: 'docx',
        png: 'png',
        jpeg: 'jpeg',
        jpg: 'jpeg',
      };
      const fileType = fileTypeMap[fileExtension] || fileExtension;

      // Get presigned URL
      console.log('[FileUpload] Getting presigned URL...');
      const presignData = await apiClient.presignUpload(file.name, fileType, file.size);
      console.log('[FileUpload] Presigned URL received, uploading to S3...');

      // Upload to S3
      const formData = new FormData();
      Object.entries(presignData.fields).forEach(([key, value]) => {
        formData.append(key, value);
      });
      formData.append('file', file);

      const xhr = new XMLHttpRequest();
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = (e.loaded / e.total) * 100;
          setProgress(percent);
          if (percent % 25 === 0) {
            console.log(`[FileUpload] Upload progress: ${Math.round(percent)}%`);
          }
        }
      });

      await new Promise<void>((resolve, reject) => {
        xhr.addEventListener('load', () => {
          console.log('[FileUpload] S3 upload complete, status:', xhr.status);
          if (xhr.status === 204 || xhr.status === 200) {
            resolve();
          } else {
            console.error('[FileUpload] S3 upload failed with status:', xhr.status);
            reject(new Error('Upload failed'));
          }
        });
        xhr.addEventListener('error', (e) => {
          console.error('[FileUpload] S3 upload error:', e);
          reject(new Error('Upload failed'));
        });
        xhr.open('POST', presignData.url);
        xhr.send(formData);
      });

      // Finalize upload
      console.log('[FileUpload] Finalizing upload...');
      const fileAsset = await apiClient.finalizeUpload(
        presignData.s3_key,
        file.name,
        fileType,
        file.size
      );

      console.log('[FileUpload] Upload complete:', {
        fileId: fileAsset.id,
        filename: fileAsset.filename,
        status: fileAsset.status,
      });
      onUploadComplete(fileAsset);
      setProgress(0);
    } catch (error: any) {
      console.error('[FileUpload] Upload error:', {
        error: error.response?.data || error.message,
        status: error.response?.status,
      });
      onError(error.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          onChange={handleFileInput}
          accept=".pdf,.txt,.docx,.png,.jpeg,.jpg"
          disabled={uploading}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer flex flex-col items-center"
        >
          <svg
            className="w-12 h-12 text-gray-400 mb-4"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="text-sm text-gray-600">
            {uploading ? 'Uploading...' : 'Drag and drop a file here, or click to select'}
          </span>
          <span className="text-xs text-gray-500 mt-2">
            PDF, TXT, DOCX, PNG, JPEG (max 10MB)
          </span>
        </label>
      </div>
      {uploading && (
        <div className="mt-4">
          <div className="bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2 text-center">{Math.round(progress)}%</p>
        </div>
      )}
    </div>
  );
}

