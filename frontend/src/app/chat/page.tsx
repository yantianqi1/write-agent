'use client';

import { useState, useEffect } from 'react';
import { ChatWorkspace } from '@/components/chat/chat-workspace';
import { BottomTabBar } from '@/components/layout/bottom-tab-bar';
import { api, type ChatMessage as APIChatMessage } from '@/lib/api';
import { StreamingStatusBadge } from '@/components/ui/progress-stream';
import { useStreamingChatState } from '@/lib/hooks';
import type { ChatMessage } from '@/lib/types';

export default function ChatPage() {
  const [isConnected, setIsConnected] = useState(false);

  // 使用流式聊天 hook
  const {
    messages,
    isStreaming,
    error,
    sessionId,
    sendMessage,
    stopStreaming,
    clearError,
    setSessionId,
  } = useStreamingChatState();

  // 初始化时检查API连接
  useEffect(() => {
    api.health.check().then(() => {
      setIsConnected(true);
    }).catch(() => {
      setIsConnected(false);
    });
  }, []);

  const handleSendMessage = async (content: string) => {
    try {
      const response = await api.chat.sendMessage({
        message: content,
        session_id: sessionId || undefined,
      });

      if (response?.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleStopGeneration = () => {
    stopStreaming();
  };

  // 准备显示的消息
  const displayMessages: ChatMessage[] = messages.length > 0
    ? messages.map(msg => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }))
    : isConnected
      ? [
          {
            id: 'welcome',
            role: 'system',
            content: '欢迎来到AI创作助手！',
            timestamp: new Date(),
          },
          {
            id: 'intro',
            role: 'assistant',
            content: '你好！我是你的AI创作助手。我们可以通过对话来创作小说，你可以随时告诉我你的想法，我会帮你实现。你想创作一个什么样的故事呢？',
            timestamp: new Date(),
          },
        ]
      : [
          {
            id: 'error',
            role: 'system',
            content: '无法连接到后端API服务。请确保后端服务已启动。',
            timestamp: new Date(),
          },
        ];

  return (
    <>
      <ChatWorkspace
        novelTitle="AI 创作助手"
        messages={displayMessages}
        onSendMessage={handleSendMessage}
        onStopGeneration={handleStopGeneration}
        isGenerating={isStreaming}
      />
      <BottomTabBar />
    </>
  );
}
