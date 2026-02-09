'use client';

/**
 * Toast 通知系统
 *
 * 提供友好的用户反馈通知
 */

import React, { createContext, useContext, useCallback, useState, useEffect, ReactNode } from 'react';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/lib/utils';

// Extract icons to avoid Turbopack import issues
const { X, CircleCheck, CircleAlert, Info, AlertTriangle } = LucideIcons as any;

/* ============================================================
   类型定义
   ============================================================ */

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  retryable?: boolean;
  onRetry?: () => void;
}

interface ToastContextType {
  toasts: Toast[];
  toast: (toast: Omit<Toast, 'id'>) => void;
  success: (message: string, title?: string) => void;
  error: (message: string, title?: string, retryAction?: () => void) => void;
  info: (message: string, title?: string) => void;
  warning: (message: string, title?: string) => void;
  remove: (id: string) => void;
  clear: () => void;
  retryable: (message: string, title?: string, onRetry?: () => void) => void;
}

/* ============================================================
   Toast Context
   ============================================================ */

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

/* ============================================================
   Toast Provider
   ============================================================ */

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const clear = useCallback(() => {
    setToasts([]);
  }, []);

  const toast = useCallback((newToast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const toastWithId: Toast = {
      ...newToast,
      id,
      duration: newToast.duration ?? 4000,
    };

    setToasts((prev) => [...prev, toastWithId]);

    // 自动移除
    if (toastWithId.duration && toastWithId.duration > 0) {
      setTimeout(() => {
        remove(id);
      }, toastWithId.duration);
    }

    return id;
  }, [remove]);

  const success = useCallback((message: string, title?: string) => {
    toast({ type: 'success', title, message });
  }, [toast]);

  const error = useCallback((message: string, title?: string) => {
    toast({ type: 'error', title, message, duration: 6000 });
  }, [toast]);

  const info = useCallback((message: string, title?: string) => {
    toast({ type: 'info', title, message });
  }, [toast]);

  const warning = useCallback((message: string, title?: string) => {
    toast({ type: 'warning', title, message, duration: 5000 });
  }, [toast]);

  // 可重试的错误通知
  const retryable = useCallback((message: string, title?: string, onRetry?: () => void) => {
    toast({
      type: 'error',
      title,
      message,
      duration: 0, // 不自动关闭
      retryable: true,
      onRetry,
      action: onRetry ? {
        label: '重试',
        onClick: () => {
          onRetry();
          remove(toasts[toasts.length - 1]?.id || '');
        },
      } : undefined,
    });
  }, [toast, remove, toasts]);

  return (
    <ToastContext.Provider
      value={{ toasts, toast, success, error, info, warning, remove, clear, retryable }}
    >
      {children}
      <ToastContainer toasts={toasts} onRemove={remove} />
    </ToastContext.Provider>
  );
}

/* ============================================================
   Toast Container
   ============================================================ */

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

/* ============================================================
   Toast Item Component
   ============================================================ */

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (!isPaused && toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        setIsExiting(true);
        setTimeout(() => onRemove(toast.id), 300);
      }, toast.duration);
      return () => clearTimeout(timer);
    }
  }, [toast.id, toast.duration, isPaused, onRemove]);

  const icons = {
    success: <CircleCheck className="w-5 h-5 text-green-500" />,
    error: <CircleAlert className="w-5 h-5 text-destructive" />,
    info: <Info className="w-5 h-5 text-blue-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-500" />,
  };

  const bgColors = {
    success: 'bg-green-50 dark:bg-green-950/50 border-green-200 dark:border-green-900',
    error: 'bg-destructive/10 border-destructive/30',
    info: 'bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-900',
    warning: 'bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-900',
  };

  return (
    <div
      className={cn(
        'pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-lg',
        'max-w-md w-full animate-slide-up',
        bgColors[toast.type],
        isExiting && 'opacity-0 translate-x-4 transition-all duration-300'
      )}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Icon */}
      <div className="shrink-0 mt-0.5">
        {icons[toast.type]}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {toast.title && (
          <h4 className="text-sm font-semibold text-foreground mb-1">
            {toast.title}
          </h4>
        )}
        <p className="text-sm text-muted-foreground">
          {toast.message}
        </p>
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={() => {
          setIsExiting(true);
          setTimeout(() => onRemove(toast.id), 300);
        }}
        className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="关闭"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

/* ============================================================
   导出便捷组件
   ============================================================ */

/**
 * 使用 Toast 的 Hook 别名，保持向后兼容
 */
export const useToasts = useToast;

/**
 * Toast 显示函数（用于组件外部）
 */
export function showToast(toast: Omit<Toast, 'id'>) {
  // 这个函数只能在组件内部使用
  // 如果需要在组件外部使用，需要创建一个全局实例
  console.warn('showToast should be used within a React component via useToast()');
}
