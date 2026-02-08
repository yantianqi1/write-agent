/**
 * Session Store
 *
 * 管理聊天会话状态的Zustand store
 * 使用 immer 中间件优化不可变更新，添加选择器防止不必要的重渲染
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import type { ChatMessage, ChatRequest, ChatResponse } from '@/lib/api';
import { api } from '@/lib/api';

// 防抖函数
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

interface SessionState {
  // 当前会话ID
  currentSessionId: string | null;

  // 消息历史 (key为sessionId)
  messages: Record<string, ChatMessage[]>;

  // 会话元数据
  sessionMetadata: Record<string, {
    title?: string;
    projectId?: string;
    createdAt?: Date;
    updatedAt?: Date;
  } | undefined>;

  // 状态
  isLoading: boolean;
  error: string | null;

  // 离线状态
  isOnline: boolean;

  // 操作方法
  sendMessage: (message: string, projectId?: string) => Promise<ChatResponse | null>;
  setSessionId: (sessionId: string) => void;
  clearSession: (sessionId?: string) => void;
  getMessages: (sessionId?: string) => ChatMessage[];

  // 清除错误
  clearError: () => void;

  // 离线检测
  checkOnlineStatus: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    immer((set, get) => ({
      // 初始状态
      currentSessionId: null,
      messages: {},
      sessionMetadata: {},
      isLoading: false,
      error: null,
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,

      // 检查在线状态
      checkOnlineStatus: () => {
        const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
        set((state) => {
          state.isOnline = isOnline;
        });
      },

      // 发送消息
      sendMessage: async (message, projectId) => {
        const state = get();

        if (!state.isOnline) {
          set((state) => {
            state.error = 'Offline mode: cannot send messages';
          });
          return null;
        }

        const sessionId = state.currentSessionId;

        // 立即添加用户消息到UI（乐观更新）
        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}-user`,
          role: 'user',
          content: message,
          timestamp: new Date(),
        };

        if (sessionId) {
          set((state) => {
            if (!state.messages[sessionId]) {
              state.messages[sessionId] = [];
            }
            state.messages[sessionId].push(userMessage);
          });
        }

        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const request: ChatRequest = {
            session_id: sessionId || undefined,
            message,
            project_id: projectId,
          };

          const response = await api.chat.sendMessage(request);

          // 保存会话ID
          if (response.session_id && response.session_id !== state.currentSessionId) {
            set((state) => {
              state.currentSessionId = response.session_id;
            });
          }

          // 添加助手回复
          const assistantMessage: ChatMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: response.message.content,
            timestamp: new Date(),
          };

          set((state) => {
            const targetSessionId = response.session_id;
            if (!state.messages[targetSessionId]) {
              state.messages[targetSessionId] = [];
            }
            // 确保用户消息在列表中
            if (!state.messages[targetSessionId].find(m => m.id === userMessage.id)) {
              state.messages[targetSessionId].push(userMessage);
            }
            state.messages[targetSessionId].push(assistantMessage);
            state.isLoading = false;
          });

          return response;
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to send message';
            state.isLoading = false;

            // 移除失败的用户消息
            if (sessionId && state.messages[sessionId]) {
              state.messages[sessionId] = state.messages[sessionId].filter(
                (m) => m.id !== userMessage.id
              );
            }
          });

          return null;
        }
      },

      // 设置会话ID
      setSessionId: (sessionId) => {
        set((state) => {
          state.currentSessionId = sessionId;
        });
      },

      // 清除会话
      clearSession: (sessionId) => {
        const state = get();
        const targetSessionId = sessionId || state.currentSessionId;

        set((state) => {
          if (targetSessionId) {
            state.messages[targetSessionId] = [];
            state.sessionMetadata[targetSessionId] = undefined;
          }
        });
      },

      // 获取消息
      getMessages: (sessionId) => {
        const state = get();
        const targetSessionId = sessionId || state.currentSessionId;
        return targetSessionId ? (state.messages[targetSessionId] || []) : [];
      },

      // 清除错误
      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },
    })),
    {
      name: 'session-storage',
      partialize: (state) => ({
        currentSessionId: state.currentSessionId,
        // 限制存储的消息数量以避免存储溢出
        messages: Object.fromEntries(
          Object.entries(state.messages).map(([sessionId, msgs]) => [
            sessionId,
            msgs.slice(-50), // 只保留最近50条消息
          ])
        ),
        sessionMetadata: state.sessionMetadata,
      }),
    }
  )
);

/* ============================================================
   选择器 - 防止不必要的重渲染
   ============================================================ */

/**
 * 获取当前会话ID
 */
export const selectCurrentSessionId = (state: SessionState) => state.currentSessionId;

/**
 * 获取当前会话的所有消息
 */
export const selectCurrentMessages = (state: SessionState) => {
  const sessionId = state.currentSessionId;
  return sessionId ? (state.messages[sessionId] || []) : [];
};

/**
 * 获取加载状态
 */
export const selectIsLoading = (state: SessionState) => state.isLoading;

/**
 * 获取错误信息
 */
export const selectError = (state: SessionState) => state.error;

/**
 * 获取在线状态
 */
export const selectIsOnline = (state: SessionState) => state.isOnline;

/**
 * 获取特定会话的消息
 */
export const selectMessagesBySessionId = (sessionId: string) => (state: SessionState) => {
  return state.messages[sessionId] || [];
};

/**
 * Hook: 使用当前会话消息（带选择器优化）
 */
export const useCurrentMessages = () => useSessionStore(selectCurrentMessages);

/**
 * Hook: 使用加载状态（带选择器优化）
 */
export const useIsLoading = () => useSessionStore(selectIsLoading);

/**
 * Hook: 使用错误状态（带选择器优化）
 */
export const useError = () => useSessionStore(selectError);

/**
 * Hook: 使用在线状态（带选择器优化）
 */
export const useIsOnline = () => useSessionStore(selectIsOnline);

// 监听在线状态
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => useSessionStore.getState().checkOnlineStatus());
  window.addEventListener('offline', () => useSessionStore.getState().checkOnlineStatus());
}
