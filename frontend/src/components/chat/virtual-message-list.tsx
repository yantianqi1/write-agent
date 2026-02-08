'use client';

/**
 * Virtual Message List Component
 *
 * 使用 react-window 实现虚拟滚动，优化长消息列表的渲染性能
 */

import { useRef, useMemo, useEffect, CSSProperties } from 'react';
import { VariableSizeList as List, ListChildComponentProps } from 'react-window';
import { cn } from '@/lib/utils';

import type { ChatMessage } from './chat-workspace';

/* ============================================================
   类型定义
   ============================================================ */

interface VirtualMessageListProps {
  messages: ChatMessage[];
  onMessageClick?: (message: ChatMessage) => void;
  className?: string;
  isGenerating?: boolean;
  TypingIndicatorComponent?: React.ComponentType;
}

interface MessageItemData {
  messages: ChatMessage[];
  onMessageClick?: (message: ChatMessage) => void;
}

/* ============================================================
   辅助函数
   ============================================================ */

/**
 * 计算消息高度（根据内容长度估算）
 * 用于动态设置虚拟列表中每项的高度
 */
function calculateMessageHeight(message: ChatMessage): number {
  const baseHeight = 80; // 基础高度（头像 + 消息容器边距）
  const lineHeight = 22; // 每行高度
  const maxWidthChars = 40; // 每行大约字符数

  // 系统消息高度较小
  if (message.role === 'system') {
    return 40;
  }

  // 计算内容行数
  const contentLines = Math.ceil(message.content.length / maxWidthChars);
  const contentHeight = Math.max(contentLines * lineHeight, 44); // 最小 44px

  // 时间戳高度
  const timestampHeight = 18;

  return baseHeight + contentHeight + timestampHeight;
}

/* ============================================================
   消息组件
   ============================================================ */

function MessageItem({
  index,
  style,
  data,
}: ListChildComponentProps<MessageItemData>) {
  const { messages, onMessageClick } = data;
  const message = messages[index];

  if (!message) return null;

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div style={style} className="flex justify-center my-4 px-4">
        <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      style={style}
      className={cn(
        'flex w-full px-4 mb-4 animate-slide-up',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div className="flex gap-3 max-w-[85%]">
        {/* Avatar */}
        {!isUser && (
          <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <span className="text-sm text-primary-foreground">✨</span>
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={cn(
            'px-4 py-3 rounded-2xl cursor-pointer transition-colors',
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-sm'
              : 'bg-card text-card-foreground rounded-bl-sm border border-border/50 hover:bg-accent/50'
          )}
          onClick={() => onMessageClick?.(message)}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
          <span className="text-[10px] opacity-60 mt-1 block">
            {message.timestamp instanceof Date
              ? message.timestamp.toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   虚拟列表组件
   ============================================================ */

export function VirtualMessageList({
  messages,
  onMessageClick,
  className,
  isGenerating = false,
  TypingIndicatorComponent,
}: VirtualMessageListProps) {
  const listRef = useRef<List>(null);
  const itemSizeCache = useRef<{ [key: string]: number }>({});

  // 计算每个项目的尺寸
  const getItemSize = (index: number) => {
    const message = messages[index];
    if (!message) return 80;

    const cacheKey = `${message.id}-${message.content.length}`;
    if (itemSizeCache.current[cacheKey]) {
      return itemSizeCache.current[cacheKey];
    }

    const height = calculateMessageHeight(message);
    itemSizeCache.current[cacheKey] = height;
    return height;
  };

  // 准备传递给列表项的数据
  const itemData = useMemo<MessageItemData>(
    () => ({
      messages,
      onMessageClick,
    }),
    [messages, onMessageClick]
  );

  // 当消息列表变化时，滚动到底部
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      // 使用 setTimeout 确保列表已更新
      setTimeout(() => {
        listRef.current?.scrollToItem(messages.length - 1, 'end');
      }, 0);
    }
  }, [messages.length]);

  // 清理缓存
  useEffect(() => {
    return () => {
      itemSizeCache.current = {};
    };
  }, [messages]);

  const isEmpty = messages.length === 0;

  if (isEmpty) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-full text-center px-8', className)}>
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4">
          <span className="text-3xl">✨</span>
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">
          开始你的创作之旅
        </h2>
        <p className="text-sm text-muted-foreground">
          通过自然对话，AI将帮助你完成小说创作
        </p>
      </div>
    );
  }

  return (
    <div className={cn('flex-1 overflow-hidden', className)}>
      <List
        ref={listRef}
        itemData={itemData}
        itemSize={getItemSize}
        itemCount={messages.length}
        width="100%"
        height="100%"
        overscanCount={3} // 预渲染上下各3个项目
      >
        {MessageItem}
      </List>
      {isGenerating && TypingIndicatorComponent && (
        <div className="flex w-full mb-4 px-4">
          <div className="flex gap-3">
            <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-sm text-primary-foreground">✨</span>
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
      )}
    </div>
  );
}

/* ============================================================
   简化版本 - 用于短列表
   ============================================================ */

interface SimpleMessageListProps {
  messages: ChatMessage[];
  onMessageClick?: (message: ChatMessage) => void;
  className?: string;
  isGenerating?: boolean;
}

/**
 * 简单的消息列表（非虚拟化）
 * 用于消息数量较少时使用（< 50 条）
 */
export function SimpleMessageList({
  messages,
  onMessageClick,
  className,
  isGenerating = false,
}: SimpleMessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-full text-center px-8', className)}>
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4">
          <span className="text-3xl">✨</span>
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">
          开始你的创作之旅
        </h2>
        <p className="text-sm text-muted-foreground">
          通过自然对话，AI将帮助你完成小说创作
        </p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className={cn('flex-1 overflow-y-auto', className)}>
      {messages.map((message) => {
        const isUser = message.role === 'user';
        const isSystem = message.role === 'system';

        if (isSystem) {
          return (
            <div key={message.id} className="flex justify-center my-4">
              <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
                {message.content}
              </span>
            </div>
          );
        }

        return (
          <div
            key={message.id}
            className={cn(
              'flex w-full mb-4 px-4 animate-slide-up',
              isUser ? 'justify-end' : 'justify-start'
            )}
          >
            <div className="flex gap-3 max-w-[85%]">
              {!isUser && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <span className="text-sm text-primary-foreground">✨</span>
                </div>
              )}
              <div
                className={cn(
                  'px-4 py-3 rounded-2xl cursor-pointer transition-colors',
                  isUser
                    ? 'bg-primary text-primary-foreground rounded-br-sm'
                    : 'bg-card text-card-foreground rounded-bl-sm border border-border/50 hover:bg-accent/50'
                )}
                onClick={() => onMessageClick?.(message)}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                  {message.content}
                </p>
                <span className="text-[10px] opacity-60 mt-1 block">
                  {message.timestamp instanceof Date
                    ? message.timestamp.toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                </span>
              </div>
            </div>
          </div>
        );
      })}
      {isGenerating && (
        <div className="flex w-full mb-4 px-4">
          <div className="flex gap-3">
            <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-sm text-primary-foreground">✨</span>
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
      )}
    </div>
  );
}

/* ============================================================
   智能消息列表 - 自动选择渲染方式
   ============================================================ */

interface SmartMessageListProps {
  messages: ChatMessage[];
  onMessageClick?: (message: ChatMessage) => void;
  className?: string;
  isGenerating?: boolean;
  virtualThreshold?: number; // 超过此数量使用虚拟滚动
}

/**
 * 智能消息列表
 * 根据消息数量自动选择是否使用虚拟滚动
 */
export function SmartMessageList({
  messages,
  onMessageClick,
  className,
  isGenerating = false,
  virtualThreshold = 50,
}: SmartMessageListProps) {
  // 如果消息数量超过阈值，使用虚拟滚动
  if (messages.length >= virtualThreshold) {
    return (
      <VirtualMessageList
        messages={messages}
        onMessageClick={onMessageClick}
        className={className}
        isGenerating={isGenerating}
      />
    );
  }

  // 否则使用简单列表
  return (
    <SimpleMessageList
      messages={messages}
      onMessageClick={onMessageClick}
      className={className}
      isGenerating={isGenerating}
    />
  );
}
