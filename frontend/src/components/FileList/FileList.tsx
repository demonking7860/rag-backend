import { useState, useEffect, useImperativeHandle, forwardRef, useRef } from 'react';
import { apiClient } from '../../services/api';
import type { FileAsset } from '../../types';

interface FileListProps {
  selectedFiles: number[];
  onFileSelect: (fileIds: number[]) => void;
  onFileDelete: (fileId: number) => void;
}

export interface FileListRef {
  refresh: () => void;
}

type FileFilter = 'all' | 'docs' | 'images' | 'failed';

const extType = (file: FileAsset) => {
  const ext = file.file_type.toLowerCase();
  if (['pdf', 'doc', 'docx', 'txt'].includes(ext)) return 'doc';
  return 'image';
};

const FileList = forwardRef<FileListRef, FileListProps>(
  ({ selectedFiles, onFileSelect, onFileDelete }, ref) => {
  const [files, setFiles] = useState<FileAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<FileFilter>('all');
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
  const filesRef = useRef<FileAsset[]>([]);
  const pageRef = useRef(1);

  const loadFiles = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      const response = await apiClient.listFiles(pageNum);
      setFiles(response.results);
      filesRef.current = response.results;
      setTotalPages(response.total_pages);
      setPage(response.page);
      pageRef.current = response.page;
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useImperativeHandle(ref, () => ({
    refresh: () => loadFiles(pageRef.current),
  }));

  useEffect(() => {
    loadFiles();
    const interval = setInterval(() => {
      // Check if any files are in processing states using ref to get current state
      if (filesRef.current.some((f) => ['processing', 'uploaded'].includes(f.status))) {
        loadFiles(pageRef.current);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const visibleFiles = files.filter((f) => {
    if (filter === 'failed') return f.status === 'failed';
    if (filter === 'docs') return extType(f) === 'doc';
    if (filter === 'images') return extType(f) === 'image';
    return true;
  });

  const hasInFlight = files.some((f) => ['processing', 'uploaded'].includes(f.status));

  const handleSelectAll = () => {
    if (selectedFiles.length === visibleFiles.length) {
      onFileSelect([]);
    } else {
      onFileSelect(visibleFiles.map((f) => f.id));
    }
  };

  const handleFileToggle = (fileId: number) => {
    if (selectedFiles.includes(fileId)) {
      onFileSelect(selectedFiles.filter((id) => id !== fileId));
    } else {
      onFileSelect([...selectedFiles, fileId]);
    }
  };

  const startRename = (file: FileAsset) => {
    setRenamingId(file.id);
    setRenameValue(file.filename);
  };

  const submitRename = async (fileId: number) => {
    if (!renameValue.trim()) return;
    try {
      await apiClient.updateFile(fileId, { filename: renameValue.trim() });
      await loadFiles(page);
    } catch (err: any) {
      setError(err.message || 'Failed to rename file');
    } finally {
      setRenamingId(null);
      setRenameValue('');
    }
  };

  const requestDelete = (fileId: number) => setPendingDeleteId(fileId);

  const confirmDelete = async (fileId: number) => {
    try {
      await apiClient.deleteFile(fileId);
      await loadFiles(page);
      onFileDelete(fileId);
    } catch (err: any) {
      setError(err.message || 'Failed to delete file');
    } finally {
      setPendingDeleteId(null);
    }
  };

  const statusClass = (status: string) =>
    status === 'ready'
      ? 'bg-green-100 text-green-800'
      : status === 'processing'
      ? 'bg-blue-100 text-blue-800'
      : status === 'failed'
      ? 'bg-red-100 text-red-800'
      : 'bg-gray-100 text-gray-800';

  if (loading && files.length === 0) {
    return <div className="text-center py-6 text-sm text-gray-500">Loading files…</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-start space-x-2 bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-lg text-xs">
          <span className="mt-0.5">⚠️</span>
          <div className="flex-1">{error}</div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 text-xs">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={visibleFiles.length > 0 && selectedFiles.length === visibleFiles.length}
              onChange={handleSelectAll}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="ml-2 text-gray-700">Select all on this page</span>
          </label>
          <span className="text-gray-500">
            {selectedFiles.length} of {visibleFiles.length} selected
          </span>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          {hasInFlight && (
            <span className="inline-flex items-center text-gray-500">
              <span className="w-2 h-2 mr-1 rounded-full bg-blue-400 animate-pulse" />
              Updating status…
            </span>
          )}
          <button
            onClick={() => loadFiles(page)}
            className="text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="flex space-x-2 text-xs">
        {(['all', 'docs', 'images', 'failed'] as FileFilter[]).map((key) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={
              'px-3 py-1 rounded-full border transition-colors ' +
              (filter === key
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50')
            }
          >
            {key === 'all' ? 'All' : key[0].toUpperCase() + key.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {visibleFiles.map((file) => {
          const isPendingDelete = pendingDeleteId === file.id;

          return (
            <div
              key={file.id}
              className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center space-x-4 flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(file.id)}
                  onChange={() => handleFileToggle(file.id)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <div className="flex-1 min-w-0">
                  {renamingId === file.id ? (
                    <div className="flex items-center space-x-2">
                      <input
                        className="border rounded px-2 py-1 text-xs w-full"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') submitRename(file.id);
                          if (e.key === 'Escape') {
                            setRenamingId(null);
                            setRenameValue('');
                          }
                        }}
                      />
                      <button
                        onClick={() => submitRename(file.id)}
                        className="text-xs text-indigo-600 hover:text-indigo-800"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setRenamingId(null);
                          setRenameValue('');
                        }}
                        className="text-xs text-gray-500 hover:text-gray-700"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.filename}</p>
                      <button
                        onClick={() => startRename(file)}
                        className="text-xs text-indigo-600 hover:text-indigo-800"
                      >
                        Rename
                      </button>
                    </div>
                  )}
                  <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                    <span>{(file.size / 1024).toFixed(1)} KB</span>
                    <span className={`px-2 py-0.5 rounded-full ${statusClass(file.status)}`}>
                      {file.status}
                    </span>
                    {file.ingestion_status !== 'complete' && (
                      <span className="text-gray-400">{file.ingestion_status}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 text-xs">
                {isPendingDelete ? (
                  <>
                    <span className="text-gray-600 mr-1">Delete this file?</span>
                    <button
                      onClick={() => confirmDelete(file.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => setPendingDeleteId(null)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => requestDelete(file.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {visibleFiles.length === 0 && !loading && (
          <div className="text-center py-8 bg-white border rounded-lg">
            <p className="text-sm font-medium text-gray-800">You don't have any files yet</p>
            <p className="mt-1 text-xs text-gray-500">
              Upload your first PDF, DOCX, TXT or image using the box above.
            </p>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 text-xs">
          <button
            onClick={() => loadFiles(page - 1)}
            disabled={page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-gray-600">
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
    </div>
  );
});

FileList.displayName = 'FileList';

export default FileList;
