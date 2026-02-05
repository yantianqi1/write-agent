'use client';

import { useState, useEffect } from 'react';
import { ChatWorkspace } from '@/components/chat/chat-workspace';
import { api, type ChatMessage as APIChatMessage } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isConnected, setIsConnected] = useState(false);

  // 初始化时检查API连接
  useEffect(() => {
    api.health.check().then(() => {
      setIsConnected(true);
      // 添加欢迎消息
      setMessages([
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
      ]);
    }).catch(() => {
      setIsConnected(false);
      setMessages([
        {
          id: 'error',
          role: 'system',
          content: '无法连接到后端API服务。请确保后端服务已启动。',
          timestamp: new Date(),
        },
      ]);
    });
  }, []);

  const handleSendMessage = async (content: string) => {
    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      setIsGenerating(true);

      const response = await api.chat.sendMessage({
        message: content,
        session_id: sessionId,
      });

      // 保存session_id
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // 添加AI响应
      const aiMessage: ChatMessage = {
        id: response.message.id || Date.now().toString(),
        role: response.message.role === 'user' ? 'user' : 'assistant',
        content: response.message.content,
        timestamp: new Date(response.message.timestamp),
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'system',
        content: error instanceof Error
          ? `错误: ${error.message}`
          : '发送消息失败，请稍后重试。',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStopGeneration = () => {
    setIsGenerating(false);
  };

  return (
    <ChatWorkspace
      novelTitle="AI 创作助手"
      messages={messages}
      onSendMessage={handleSendMessage}
      onStopGeneration={handleStopGeneration}
      isGenerating={isGenerating}
    />
  );
}
