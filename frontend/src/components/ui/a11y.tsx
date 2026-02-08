'use client';

/**
 * 可访问性组件
 *
 * 提供屏幕阅读器支持、键盘导航和焦点管理
 */

import React, { useEffect, useRef, useState, useCallback, ReactNode, cloneElement, Children } from 'react';
import { cn } from '@/lib/utils';

/* ============================================================
   Live Region - 屏幕阅读器通知区域
   ============================================================ */

export interface LiveRegionProps extends React.HTMLAttributes<HTMLDivElement> {
  role?: 'status' | 'alert' | 'log';
  message: string;
  ariaLive?: 'polite' | 'assertive' | 'off';
  clearOnUnmount?: boolean;
}

/**
 * 屏幕阅读器通知组件
 *
 * 用于向屏幕阅读器宣布动态内容变化，对视觉用户不可见
 */
export function LiveRegion({
  role = 'status',
  message,
  ariaLive = 'polite',
  clearOnUnmount = false,
  className,
  ...props
}: LiveRegionProps) {
  const [announcement, setAnnouncement] = useState(message);

  useEffect(() => {
    setAnnouncement(message);
  }, [message]);

  useEffect(() => {
    if (clearOnUnmount) {
      return () => {
        setAnnouncement('');
      };
    }
  }, [clearOnUnmount]);

  return (
    <div
      role={role}
      aria-live={ariaLive}
      aria-atomic="true"
      className={cn('sr-only', className)}
      {...props}
    >
      {announcement}
    </div>
  );
}

/* ============================================================
   Focus Trap - 焦点陷阱
   ============================================================ */

export interface FocusTrapProps {
  children: ReactNode;
  active?: boolean;
  onEscape?: () => void;
  initialFocus?: React.RefObject<HTMLElement>;
  restoreFocus?: boolean;
  className?: string;
}

/**
 * 焦点陷阱组件
 *
 * 将Tab焦点限制在子元素内，用于模态框、对话框等场景
 */
export function FocusTrap({
  children,
  active = true,
  onEscape,
  initialFocus,
  restoreFocus = true,
  className,
}: FocusTrapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // 获取所有可聚焦元素
  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(focusableSelectors)
    ).filter(el => el.offsetParent !== null); // 只返回可见元素
  }, []);

  // 焦点处理
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!active) return;

      if (e.key === 'Escape' && onEscape) {
        onEscape();
        return;
      }

      if (e.key !== 'Tab') return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Shift + Tab
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      }
      // Tab
      else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    },
    [active, getFocusableElements, onEscape]
  );

  // 激活时处理焦点
  useEffect(() => {
    if (!active) return;

    // 保存之前的焦点元素
    previousActiveElement.current = document.activeElement as HTMLElement;

    // 设置初始焦点
    if (initialFocus?.current) {
      initialFocus.current.focus();
    } else {
      // 如果没有指定初始焦点，聚焦到第一个可聚焦元素
      const focusableElements = getFocusableElements();
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // 恢复之前的焦点
      if (restoreFocus && previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [active, handleKeyDown, initialFocus, restoreFocus, getFocusableElements]);

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  );
}

/* ============================================================
   Skip Link - 跳过导航链接
   ============================================================ */

export interface SkipLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  targetId: string;
  label?: string;
}

/**
 * 跳过导航链接
 *
 * 允许键盘用户跳过重复的导航内容，直接访问主要内容
 */
export function SkipLink({ targetId, label = '跳到主要内容', className, ...props }: SkipLinkProps) {
  return (
    <a
      href={`#${targetId}`}
      className={cn(
        'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4',
        'focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground',
        'focus:rounded focus:ring-2 focus:ring-ring focus:ring-offset-2',
        'focus:outline-none',
        className
      )}
      {...props}
    >
      {label}
    </a>
  );
}

/* ============================================================
   Visually Hidden - 视觉隐藏但可被屏幕阅读器访问
   ============================================================ */

export interface VisuallyHiddenProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  focusable?: boolean;
}

/**
 * 视觉隐藏组件
 *
 * 对视觉用户隐藏，但对屏幕阅读器和键盘用户可见
 */
export function VisuallyHidden({ children, focusable = false, className, ...props }: VisuallyHiddenProps) {
  return (
    <span
      className={cn(
        'sr-only',
        focusable && 'focus:not-sr-only focus:absolute focus:z-50',
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

/* ============================================================
   Announcer - 状态通知器
   ============================================================ */

interface Announcement {
  id: string;
  message: string;
  type: 'status' | 'alert';
}

const announcerContext = React.createContext<{
  announce: (message: string, type?: 'status' | 'alert') => void;
}>({
  announce: () => {},
});

/**
 * Announcer Provider
 */
export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  const announce = useCallback((message: string, type: 'status' | 'alert' = 'status') => {
    const id = Date.now().toString();
    setAnnouncements(prev => [...prev, { id, message, type }]);

    // 清除通知
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(a => a.id !== id));
    }, 1000);
  }, []);

  return (
    <announcerContext.Provider value={{ announce }}>
      {children}
      {/* Status 通知区域 */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announcements.filter(a => a.type === 'status').map(a => a.message).join(', ')}
      </div>
      {/* Alert 通知区域 */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {announcements.filter(a => a.type === 'alert').map(a => a.message).join(', ')}
      </div>
    </announcerContext.Provider>
  );
}

/**
 * 使用通知器
 */
export function useAnnouncer() {
  return React.useContext(announcerContext);
}

/* ============================================================
   Focus Management Hooks
   ============================================================ */

/**
 * 焦点重置 Hook
 *
 * 组件卸载时恢复焦点到之前聚焦的元素
 */
export function useFocusReset(active: boolean = true) {
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active) return;

    previousActiveElement.current = document.activeElement as HTMLElement;

    return () => {
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [active]);
}

/**
 * 自动聚焦 Hook
 *
 * 挂载时自动聚焦到指定元素
 */
export function useAutoFocus(
  enabled: boolean = true,
  delay: number = 0
) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!enabled || !ref.current) return;

    const timer = setTimeout(() => {
      ref.current?.focus();
    }, delay);

    return () => clearTimeout(timer);
  }, [enabled, delay]);

  return ref;
}

/* ============================================================
   Keyboard Navigation Hooks
   ============================================================ */

export type KeyboardDirection = 'horizontal' | 'vertical' | 'both' | 'grid';

export interface UseKeyboardNavigationOptions {
  direction?: KeyboardDirection;
  loop?: boolean;
  onChange?: (index: number) => void;
  onEnter?: (index: number) => void;
  onEscape?: () => void;
  isActive?: boolean;
}

export interface UseKeyboardNavigationReturn {
  currentIndex: number;
  onKeyDown: (e: React.KeyboardEvent) => void;
  setCurrentIndex: (index: number) => void;
}

/**
 * 键盘导航 Hook
 *
 * 使用方向键在子元素间导航
 */
export function useKeyboardNavigation(
  itemCount: number,
  options: UseKeyboardNavigationOptions = {}
): UseKeyboardNavigationReturn {
  const {
    direction = 'vertical',
    loop = true,
    onChange,
    onEnter,
    onEscape,
    isActive = true,
  } = options;

  const [currentIndex, setCurrentIndex] = useState(0);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isActive) return;

      let newIndex = currentIndex;

      switch (e.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          e.preventDefault();
          if (direction !== 'vertical' && direction !== 'horizontal' && direction !== 'both') {
            break;
          }
          if (direction === 'vertical' && e.key === 'ArrowRight') {
            break;
          }
          if (direction === 'horizontal' && e.key === 'ArrowDown') {
            break;
          }
          newIndex = currentIndex + 1;
          if (newIndex >= itemCount) {
            newIndex = loop ? 0 : itemCount - 1;
          }
          break;

        case 'ArrowUp':
        case 'ArrowLeft':
          e.preventDefault();
          if (direction !== 'vertical' && direction !== 'horizontal' && direction !== 'both') {
            break;
          }
          if (direction === 'vertical' && e.key === 'ArrowLeft') {
            break;
          }
          if (direction === 'horizontal' && e.key === 'ArrowUp') {
            break;
          }
          newIndex = currentIndex - 1;
          if (newIndex < 0) {
            newIndex = loop ? itemCount - 1 : 0;
          }
          break;

        case 'Home':
          e.preventDefault();
          newIndex = 0;
          break;

        case 'End':
          e.preventDefault();
          newIndex = itemCount - 1;
          break;

        case 'Enter':
        case ' ':
          e.preventDefault();
          onEnter?.(currentIndex);
          return;

        case 'Escape':
          e.preventDefault();
          onEscape?.();
          return;

        default:
          return;
      }

      if (newIndex !== currentIndex) {
        setCurrentIndex(newIndex);
        onChange?.(newIndex);
      }
    },
    [
      currentIndex,
      itemCount,
      direction,
      loop,
      isActive,
      onChange,
      onEnter,
      onEscape,
    ]
  );

  return {
    currentIndex,
    onKeyDown: handleKeyDown,
    setCurrentIndex,
  };
}

/* ============================================================
   Focusable Item Wrapper
   ============================================================ */

export interface FocusableItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  focused?: boolean;
  index?: number;
}

/**
 * 可聚焦项包装器
 *
 * 自动添加必要的可访问性属性
 */
export function FocusableItem({ children, focused, index, className, ...props }: FocusableItemProps) {
  const child = Children.only(children) as React.ReactElement;

  return cloneElement(child, {
    ...props,
    tabIndex: focused ? 0 : -1,
    'data-index': index,
    className: cn(
      'outline-none',
      focused && 'ring-2 ring-ring ring-offset-2',
      className,
      child.props.className
    ),
  } as any);
}

/* ============================================================
   键盘焦点集合组件
   ============================================================ */

export interface FocusCollectionProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  direction?: KeyboardDirection;
  loop?: boolean;
  active?: boolean;
  onIndexChange?: (index: number) => void;
  onItemActivate?: (index: number) => void;
}

/**
 * 键盘可导航集合组件
 *
 * 使子元素可以通过键盘导航
 */
export function FocusCollection({
  children,
  direction = 'vertical',
  loop = true,
  active = true,
  onIndexChange,
  onItemActivate,
  className,
  ...props
}: FocusCollectionProps) {
  const items = Children.toArray(children);
  const { currentIndex, onKeyDown } = useKeyboardNavigation(items.length, {
    direction,
    loop,
    isActive: active,
    onChange: onIndexChange,
    onEnter: onItemActivate,
  });

  return (
    <div
      role="listbox"
      tabIndex={0}
      onKeyDown={onKeyDown}
      className={className}
      {...props}
    >
      {items.map((child, index) => (
        <FocusableItem key={index} focused={index === currentIndex} index={index}>
          {child}
        </FocusableItem>
      ))}
    </div>
  );
}

export default {
  LiveRegion,
  FocusTrap,
  SkipLink,
  VisuallyHidden,
  AnnouncerProvider,
  useAnnouncer,
  useFocusReset,
  useAutoFocus,
  useKeyboardNavigation,
  FocusableItem,
  FocusCollection,
};
