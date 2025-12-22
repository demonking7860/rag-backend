import { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import FileUpload from '../FileUpload/FileUpload';
import FileList from '../FileList/FileList';
import ChatInterface from '../Chat/ChatInterface';
import type { FileAsset } from '../../types';

export default function Dashboard() {
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleUploadComplete = (file: FileAsset) => {
    setUploadSuccess(`File "${file.filename}" uploaded successfully!`);
    setUploadError('');
    setTimeout(() => setUploadSuccess(''), 3000);
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
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">File-Chat RAG</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.username}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - File Management */}
          <div className="lg:col-span-1 space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Files</h2>
              {uploadError && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                  {uploadError}
                </div>
              )}
              {uploadSuccess && (
                <div className="mb-4 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
                  {uploadSuccess}
                </div>
              )}
              <FileUpload
                onUploadComplete={handleUploadComplete}
                onError={handleUploadError}
              />
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Files</h2>
              <FileList
                selectedFiles={selectedFiles}
                onFileSelect={setSelectedFiles}
                onFileDelete={handleFileDelete}
              />
            </div>
          </div>

          {/* Right Column - Chat */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border h-[calc(100vh-12rem)] flex flex-col">
              <div className="border-b p-4">
                <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
                {selectedFiles.length > 0 && (
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedFiles.length} file(s) selected for chat
                  </p>
                )}
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
      </div>
    </div>
  );
}

