export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface FileAsset {
  id: number;
  filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  status: 'pending' | 'uploaded' | 'processing' | 'ready' | 'failed' | 'deletion_failed';
  ingestion_status: 'not_started' | 'in_progress' | 'partial' | 'complete' | 'failed';
  deletion_failed: boolean;
  metadata: Record<string, any>;
}

export interface FileListResponse {
  results: FileAsset[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PresignResponse {
  url: string;
  fields: Record<string, string>;
  s3_key: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  file_ids: number[];
  created_at: string;
}

export interface Citation {
  filename: string;
  page_number?: number;
}

export interface ChatResponse {
  conversation_id: number;
  message: Message;
  response: Message;
  citations: Citation[];
}

export interface Conversation {
  id: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

