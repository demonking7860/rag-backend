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
  const streamingIntervalRef = useRef<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      console.log('[Chat] Sending message');

      const response = await apiClient.sendMessage(
        userMessage,
        currentConversationId,
        selectedFileIds.length > 0 ? selectedFileIds : undefined
      );

      // Update conversation ID if new conversation was created
      if (response.conversation_id !== currentConversationId) {
        setCurrentConversationId(response.conversation_id);
        onConversationChange?.(response.conversation_id);
      }

      // Replace temp message with actual message and add response placeholder
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
        const assistantMsg: Message = {
          ...response.response,
          citations: response.citations || [],
          content: '',
        };
        return [...filtered, response.message, assistantMsg];
      });

      // Pseudo-streaming: reveal assistant text gradually
      const fullText = response.response.content || '';
      if (fullText.length === 0) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === response.response.id ? { ...m, content: fullText, citations: response.citations || [] } : m
          )
        );
      } else {
        let index = 0;
        const step = Math.max(10, Math.floor(fullText.length / 30));
        if (streamingIntervalRef.current) clearInterval(streamingIntervalRef.current);
        streamingIntervalRef.current = window.setInterval(() => {
          index = Math.min(fullText.length, index + step);
          const partial = fullText.slice(0, index);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === response.response.id ? { ...m, content: partial, citations: response.citations || [] } : m
            )
          );
          if (index >= fullText.length && streamingIntervalRef.current) {
            clearInterval(streamingIntervalRef.current);
            streamingIntervalRef.current = null;
          }
        }, 30);
      }
    } catch (error: any) {
      console.error('[Chat] Error sending message');

      // Simple error message the user can see
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
      <div className="mt-2 text-xs text-gray-500">
        <span className="font-semibold mr-1">Sources:</span>
        {citations.map((c, idx) => (
          <span key={idx}>
            {idx > 0 && ', '}
            {c.filename}
            {c.page_number && ` (p. ${c.page_number})`}
          </span>
        ))}
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

        {messages.map((message) => {
          const isUser = message.role === 'user';
          return (
            <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className="flex items-start space-x-2 max-w-2xl">
                <div
                  className={
                    'w-7 h-7 rounded-full flex items-center justify-center text-xs ' +
                    (isUser ? 'bg-gray-400 text-white' : 'bg-indigo-500 text-white')
                  }
                >
                  {isUser ? 'U' : 'B'}
                </div>
                <div
                  className={
                    'rounded-lg px-4 py-2 text-sm ' +
                    (isUser ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-900')
                  }
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.role === 'assistant' && renderCitations(message.citations || [])}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start mt-2 px-4">
            <div className="flex items-center text-xs text-gray-500 space-x-1">
              <span>Answering</span>
              <span className="flex space-x-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
                <span
                  className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.15s' }}
                />
                <span
                  className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.3s' }}
                />
              </span>
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

