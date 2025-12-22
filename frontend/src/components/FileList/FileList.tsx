import { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import type { FileAsset } from '../../types';

interface FileListProps {
  selectedFiles: number[];
  onFileSelect: (fileIds: number[]) => void;
  onFileDelete: (fileId: number) => void;
}

export default function FileList({ selectedFiles, onFileSelect, onFileDelete }: FileListProps) {
  const [files, setFiles] = useState<FileAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');

  const loadFiles = async (pageNum: number = 1) => {
    try {
      console.log('[FileList] Loading files, page:', pageNum);
      setLoading(true);
      const response = await apiClient.listFiles(pageNum);
      console.log('[FileList] Files loaded:', {
        count: response.results.length,
        totalPages: response.total_pages,
        page: response.page,
      });
      setFiles(response.results);
      setTotalPages(response.total_pages);
      setPage(response.page);
    } catch (err: any) {
      console.error('[FileList] Load files failed:', {
        page: pageNum,
        error: err.response?.data || err.message,
        status: err.response?.status,
      });
      setError(err.message || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleSelectAll = () => {
    if (selectedFiles.length === files.length) {
      onFileSelect([]);
    } else {
      onFileSelect(files.map((f) => f.id));
    }
  };

  const handleFileToggle = (fileId: number) => {
    if (selectedFiles.includes(fileId)) {
      onFileSelect(selectedFiles.filter((id) => id !== fileId));
    } else {
      onFileSelect([...selectedFiles, fileId]);
    }
  };

  const handleDelete = async (fileId: number) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        console.log('[FileList] Deleting file:', fileId);
        await apiClient.deleteFile(fileId);
        console.log('[FileList] File deleted successfully');
        await loadFiles(page);
        onFileDelete(fileId);
      } catch (err: any) {
        console.error('[FileList] Delete failed:', {
          fileId,
          error: err.response?.data || err.message,
        });
        setError(err.message || 'Failed to delete file');
      }
    }
  };

  const handleRetry = async (fileId: number) => {
    try {
      console.log('[FileList] Retrying file processing:', fileId);
      await apiClient.retryFinalize(fileId);
      console.log('[FileList] Retry initiated successfully');
      await loadFiles(page);
    } catch (err: any) {
      console.error('[FileList] Retry failed:', {
        fileId,
        error: err.response?.data || err.message,
      });
      setError(err.message || 'Failed to retry processing');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      ready: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
      uploaded: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading && files.length === 0) {
    return <div className="text-center py-8">Loading files...</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={files.length > 0 && selectedFiles.length === files.length}
              onChange={handleSelectAll}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="ml-2 text-sm text-gray-700">Select All</span>
          </label>
          <span className="text-sm text-gray-600">
            {selectedFiles.length} of {files.length} selected
          </span>
        </div>
        <button
          onClick={() => loadFiles(page)}
          className="text-sm text-indigo-600 hover:text-indigo-800"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.id}
            className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
          >
            <div className="flex items-center space-x-4 flex-1">
              <input
                type="checkbox"
                checked={selectedFiles.includes(file.id)}
                onChange={() => handleFileToggle(file.id)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{file.filename}</p>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${getStatusColor(file.status)}`}>
                    {file.status}
                  </span>
                  {file.ingestion_status !== 'complete' && (
                    <span className="text-xs text-gray-500">
                      {file.ingestion_status}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {file.status === 'uploaded' && file.ingestion_status === 'failed' && (
                <button
                  onClick={() => handleRetry(file.id)}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Retry
                </button>
              )}
              <button
                onClick={() => handleDelete(file.id)}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => loadFiles(page - 1)}
            disabled={page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => loadFiles(page + 1)}
            disabled={page === totalPages}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {files.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          No files uploaded yet
        </div>
      )}
    </div>
  );
}

