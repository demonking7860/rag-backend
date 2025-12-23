import { useState, useRef } from 'react';
import { useAuthStore } from '../../store/authStore';
import FileUpload from '../FileUpload/FileUpload';
import FileList, { FileListRef } from '../FileList/FileList';
import ChatInterface from '../Chat/ChatInterface';
import type { FileAsset } from '../../types';

export default function Dashboard() {
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const fileListRef = useRef<FileListRef>(null);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleUploadComplete = (file: FileAsset) => {
    setUploadSuccess(`File "${file.filename}" uploaded successfully.`);
    setUploadError('');
    setTimeout(() => setUploadSuccess(''), 3000);
    // Immediately refresh the file list to show the new file
    setTimeout(() => {
      fileListRef.current?.refresh();
    }, 500);
  };

  const handleUploadError = (error: string) => {
    setUploadError(error);
    setUploadSuccess('');
    setTimeout(() => setUploadError(''), 5000);
  };

  const handleFileDelete = (fileId: number) => {
    setSelectedFiles((prev) => prev.filter((id) => id !== fileId));
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">File-Chat RAG</h1>
          <div className="flex items-center space-x-3 text-sm">
            <span className="text-gray-600">
              Signed in as <span className="font-medium">{user?.username}</span>
            </span>
            <button
              onClick={logout}
              className="px-3 py-1 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors duration-150"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column: upload + files */}
          <div className="lg:col-span-1 space-y-5">
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <h2 className="text-sm font-semibold text-gray-900 mb-3">Upload files</h2>
              {uploadError && (
                <div className="mb-3 bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-xs">
                  {uploadError}
                </div>
              )}
              {uploadSuccess && (
                <div className="mb-3 bg-green-50 border border-green-200 text-green-800 px-3 py-2 rounded text-xs">
                  {uploadSuccess}
                </div>
              )}
              <FileUpload onUploadComplete={handleUploadComplete} onError={handleUploadError} />
            </div>

            <div className="bg-white rounded-xl shadow-sm border p-4">
              <h2 className="text-sm font-semibold text-gray-900 mb-3">Your files</h2>
              <FileList
                ref={fileListRef}
                selectedFiles={selectedFiles}
                onFileSelect={setSelectedFiles}
                onFileDelete={handleFileDelete}
              />
            </div>
          </div>

          {/* Right column: chat */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border h-[calc(100vh-9rem)] flex flex-col">
              <div className="border-b px-4 py-3">
                <h2 className="text-sm font-semibold text-gray-900">Chat</h2>
                <p className="text-xs text-gray-500 mt-1">
                  {selectedFiles.length > 0
                    ? `Chatting about ${selectedFiles.length} selected file(s)`
                    : 'Chatting about all files'}
                </p>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  selectedFileIds={selectedFiles}
                  conversationId={conversationId}
                  onConversationChange={setConversationId}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

