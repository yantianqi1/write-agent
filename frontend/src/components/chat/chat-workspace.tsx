'use client';

import { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Send, Square, Plus, Sparkles, ChevronLeft } from 'lucide-react';
import { SmartMessageList } from './virtual-message-list';

/* ============================================================
   Chat Message Component
   ============================================================ */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  contextRef?: {
    type: 'chapter' | 'character' | 'setting' | 'plot';
    id: string;
    title: string;
  };
}

export interface ChatMessageProps {
  message: ChatMessage;
}

/* 使用 React.memo 包装消息组件，避免不必要的重新渲染 */
const ChatMessageComponent = memo(function ChatMessageComponentInner({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  // 使用 useMemo 缓存时间戳格式化结果
  const timeString = useMemo(
    () => message.timestamp.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    [message.timestamp]
  );

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex w-full mb-4 animate-slide-up',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div className="flex gap-3 max-w-[85%]">
        {/* Avatar */}
        {!isUser && (
          <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center" aria-hidden="true">
            <Sparkles className="w-4 h-4 text-primary-foreground" />
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={cn(
            'px-4 py-3 rounded-2xl',
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-sm'
              : 'bg-card text-card-foreground rounded-bl-sm border border-border/50'
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
          <span className="text-[10px] opacity-60 mt-1 block">
            {timeString}
          </span>
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // 自定义比较函数：只有当消息ID和内容相同时才认为是相同的props
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.message.content === nextProps.message.content &&
    prevProps.message.role === nextProps.message.role
  );
});

/* ============================================================
   Typing Indicator
   ============================================================ */

/* 使用 React.memo 包装输入指示器组件 */
const TypingIndicator = memo(function TypingIndicatorInner() {
  return (
    <div className="flex w-full mb-4">
      <div className="flex gap-3">
        <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center" aria-hidden="true">
          <Sparkles className="w-4 h-4 text-primary-foreground" />
        </div>
        <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-card border border-border/50">
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-pulse delay-100" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-pulse delay-200" />
          </div>
        </div>
      </div>
    </div>
  );
});

/* ============================================================
   Chat Workspace Component - Main
   ============================================================ */

export interface ChatWorkspaceProps {
  novelId?: string;
  novelTitle?: string;
  messages?: ChatMessage[];
  onSendMessage?: (content: string) => void;
  onStopGeneration?: () => void;
  isGenerating?: boolean;
}

export function ChatWorkspace({
  novelId,
  novelTitle = '未命名作品',
  messages: initialMessages = [],
  onSendMessage,
  onStopGeneration,
  isGenerating = false,
}: ChatWorkspaceProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync messages from parent (store)
  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // 使用 useCallback 缓存事件处理函数
  const handleSend = useCallback(() => {
    if (!input.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInput('');

    if (onSendMessage) {
      onSendMessage(input.trim());
    }
  }, [input, onSendMessage]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  }, []);

  const handleClearInput = useCallback(() => {
    setInput('');
    inputRef.current?.focus();
  }, []);

  // 使用 useMemo 缓存建议选项
  const suggestions = useMemo(
    () => [
      { icon: '📖', text: '续写下一章' },
      { icon: '✨', text: '优化这段文字' },
      { icon: '👤', text: '添加新角色' },
      { icon: '🌍', text: '完善世界观' },
    ],
    []
  );

  // 使用 useMemo 缓存建议按钮点击处理
  const handleSuggestionClick = useCallback((text: string) => {
    setInput(text);
    inputRef.current?.focus();
  }, []);

  return (
    <div className="flex flex-col h-[calc(100dvh-4rem)] bg-background">
      {/* Header */}
      <header className="shrink-0 glass border-b border-border/20 safe-top">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Back Button */}
            <button
              onClick={() => router.push('/')}
              className="flex items-center justify-center w-8 h-8 -ml-2 rounded-full touch-hover hover:bg-muted/50 transition-colors"
              aria-label="返回"
            >
              <ChevronLeft className="w-5 h-5 text-foreground" />
            </button>
            <div className="min-w-0">
              <h1 className="text-base font-semibold text-foreground truncate">{novelTitle}</h1>
              <p className="text-xs text-muted-foreground truncate">
                {isGenerating ? '正在生成中...' : 'AI 创作助手'}
              </p>
            </div>
          </div>
          <Button size="sm" variant="ghost" className="shrink-0">
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Messages Area */}
      {messages.length === 0 ? (
        <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-ios">
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2">
              开始你的创作之旅
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              通过自然对话，AI将帮助你完成小说创作
            </p>

            {/* Suggestions */}
            <div className="grid grid-cols-2 gap-3 w-full max-w-xs">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  className={cn(
                    'flex flex-col items-center gap-2 p-4',
                    'rounded-2xl bg-card border border-border/50',
                    'touch-hover transition-all duration-150'
                  )}
                  type="button"
                >
                  <span className="text-2xl" aria-hidden="true">{suggestion.icon}</span>
                  <span className="text-xs text-foreground">{suggestion.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <SmartMessageList
          messages={messages}
          isGenerating={isGenerating}
          className="px-4 py-4"
          virtualThreshold={50}
        />
      )}

      {/* Input Area */}
      <div className="shrink-0 glass border-t border-border/20">
        <div className="p-4">
          {isGenerating ? (
            <Button
              variant="danger"
              className="w-full"
              onClick={onStopGeneration}
            >
              <Square className="w-4 h-4 mr-2" />
              停止生成
            </Button>
          ) : (
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Input
                  ref={inputRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder="输入你想说的..."
                  className="pr-12"
                  aria-label="输入消息"
                />
                {input.length > 0 && (
                  <button
                    onClick={handleClearInput}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    type="button"
                    aria-label="清空输入"
                  >
                    <span className="text-xs">✕</span>
                  </button>
                )}
              </div>
              <Button
                onClick={handleSend}
                disabled={!input.trim()}
                className="shrink-0 aspect-square h-12 rounded-2xl"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          )}
          <p className="text-[10px] text-muted-foreground text-center mt-2">
            AI生成内容仅供参考，请自行判断和修改
          </p>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   Quick Action Buttons
   ============================================================ */

export interface QuickActionsProps {
  onContinue: () => void;
  onExpand: () => void;
  onRewrite: () => void;
  onOutline: () => void;
  disabled?: boolean;
}

export function QuickActions({ onContinue, onExpand, onRewrite, onOutline, disabled }: QuickActionsProps) {
  const actions = [
    { label: '续写', icon: '▶', onClick: onContinue },
    { label: '扩写', icon: '↔', onClick: onExpand },
    { label: '重写', icon: '↻', onClick: onRewrite },
    { label: '大纲', icon: '≡', onClick: onOutline },
  ];

  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {actions.map((action, index) => (
        <Button
          key={index}
          size="sm"
          variant="secondary"
          onClick={action.onClick}
          disabled={disabled}
          className="shrink-0 rounded-xl"
        >
          <span className="mr-1">{action.icon}</span>
          {action.label}
        </Button>
      ))}
    </div>
  );
}
