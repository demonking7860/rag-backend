import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../../services/api';
import type { Message, Citation } from '../../types';

interface ChatInterfaceProps {
  selectedFileIds: number[];
  conversationId?: number;
  onConversationChange?: (conversationId: number) => void;
}

export default function ChatInterface({
  selectedFileIds,
  conversationId,
  onConversationChange,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<number | undefined>(
    conversationId
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  useEffect(() => {
    if (conversationId && conversationId !== currentConversationId) {
      loadConversationHistory(conversationId);
      setCurrentConversationId(conversationId);
    }
  }, [conversationId]);

  const loadConversationHistory = async (convId: number) => {
    try {
      console.log('[Chat] Loading conversation history:', convId);
      const conversation = await apiClient.getConversationHistory(convId);
      console.log('[Chat] Conversation loaded:', {
        conversationId: convId,
        messageCount: conversation.messages?.length || 0,
      });
      setMessages(conversation.messages);
      setCurrentConversationId(convId);
    } catch (error: any) {
      console.error('[Chat] Failed to load conversation history:', {
        conversationId: convId,
        error: error.response?.data || error.message,
      });
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);
    setStreaming(false);
    setStreamingText('');

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      file_ids: selectedFileIds,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      console.log('[Chat] Sending message:', {
        message: userMessage.substring(0, 50),
        conversationId: currentConversationId,
        selectedFileIds,
      });
      
      // For now, use non-streaming (streaming can be added later)
      const response = await apiClient.sendMessage(
        userMessage,
        currentConversationId,
        selectedFileIds.length > 0 ? selectedFileIds : undefined
      );

      console.log('[Chat] Response received:', {
        conversationId: response.conversation_id,
        responseLength: response.response?.content?.length || 0,
        citationsCount: response.citations?.length || 0,
      });

      // Update conversation ID if new conversation was created
      if (response.conversation_id !== currentConversationId) {
        console.log('[Chat] New conversation created:', response.conversation_id);
        setCurrentConversationId(response.conversation_id);
        onConversationChange?.(response.conversation_id);
      }

      // Replace temp message with actual message and add response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
        return [...filtered, response.message, response.response];
      });
    } catch (error: any) {
      console.error('[Chat] Error sending message:', {
        error: error.response?.data || error.message,
        status: error.response?.status,
        conversationId: currentConversationId,
        selectedFileIds,
      });
      // Add error message
      const errorMessage: Message = {
        id: Date.now(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        file_ids: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
        return [...filtered, errorMessage];
      });
    } finally {
      setLoading(false);
    }
  };

  const renderCitations = (citations: Citation[]) => {
    if (!citations || citations.length === 0) return null;

    return (
      <div className="mt-2 space-y-1">
        <p className="text-xs font-semibold text-gray-600">Sources:</p>
        <div className="flex flex-wrap gap-2">
          {citations.map((citation, idx) => (
            <span
              key={idx}
              className="inline-flex items-center px-2 py-1 rounded-md bg-indigo-100 text-indigo-800 text-xs"
            >
              {citation.filename}
              {citation.page_number && ` (p. ${citation.page_number})`}
            </span>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-2">
              {selectedFileIds.length > 0
                ? `Chatting about ${selectedFileIds.length} selected file(s)`
                : 'Ask questions about your uploaded files'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.role === 'assistant' && message.file_ids && message.file_ids.length > 0 && (
                <div className="mt-2 text-xs text-gray-600">
                  Referenced {message.file_ids.length} file(s)
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}

        {streaming && streamingText && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-3xl">
              <p className="whitespace-pre-wrap">{streamingText}</p>
              <span className="animate-pulse">▋</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
        {selectedFileIds.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            Chatting about {selectedFileIds.length} selected file(s)
          </p>
        )}
      </form>
    </div>
  );
}

