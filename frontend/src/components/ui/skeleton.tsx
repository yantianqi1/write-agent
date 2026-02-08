/**
 * Skeleton Screen Components
 *
 * Loading placeholders that mimic the structure of actual content,
 * providing a better perceived loading experience.
 */

import { cn } from '@/lib/utils';

/* ============================================================
   Base Skeleton Component
   ============================================================ */

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
  animation = 'pulse',
  ...props
}: SkeletonProps) {
  const variantStyles = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-md',
  };

  const animationStyles = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer',
    none: '',
  };

  return (
    <div
      className={cn(
        'bg-muted',
        variantStyles[variant],
        animationStyles[animation],
        className
      )}
      style={{ width, height }}
      {...props}
    />
  );
}

/* ============================================================
   Card Skeleton
   ============================================================ */

export interface CardSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  showAvatar?: boolean;
  lines?: number;
}

export function CardSkeleton({
  className,
  showAvatar = true,
  lines = 3,
  ...props
}: CardSkeletonProps) {
  return (
    <div className={cn('bg-card rounded-2xl p-4 border border-border/50', className)} {...props}>
      <div className="flex gap-3">
        {showAvatar && (
          <Skeleton
            variant="circular"
            width={48}
            height={48}
            className="shrink-0"
          />
        )}
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={20} className="mb-2" />
          <Skeleton width="100%" />
          <Skeleton width="90%" />
          {lines > 2 && <Skeleton width="80%" />}
          {lines > 3 && <Skeleton width="70%" />}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   Chat Skeleton
   ============================================================ */

export interface ChatSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'user' | 'assistant';
}

export function ChatSkeleton({
  className,
  variant = 'assistant',
  ...props
}: ChatSkeletonProps) {
  const isAssistant = variant === 'assistant';

  return (
    <div
      className={cn(
        'flex w-full mb-4',
        !isAssistant && 'justify-end'
      )}
      {...props}
    >
      <div className={cn('flex gap-3 max-w-[85%]', !isAssistant && 'flex-row-reverse')}>
        {isAssistant && (
          <Skeleton variant="circular" width={32} height={32} className="shrink-0" />
        )}
        <div
          className={cn(
            'px-4 py-3 rounded-2xl space-y-2',
            isAssistant
              ? 'bg-muted/50 rounded-bl-sm'
              : 'bg-primary/20 rounded-br-sm'
          )}
        >
          <Skeleton width={120} height={14} />
          <Skeleton width="100%" height={14} />
          <Skeleton width="90%" height={14} />
          <Skeleton width="60%" height={14} />
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   Text Skeleton
   ============================================================ */

export interface TextSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  lines?: number;
  className?: string;
}

export function TextSkeleton({
  lines = 3,
  className,
  ...props
}: TextSkeletonProps) {
  return (
    <div className={cn('space-y-2', className)} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '70%' : '100%'}
          height={16}
        />
      ))}
    </div>
  );
}

/* ============================================================
   Project Card Skeleton (for home page)
   ============================================================ */

export interface ProjectCardSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  showProgress?: boolean;
}

export function ProjectCardSkeleton({
  className,
  showProgress = false,
  ...props
}: ProjectCardSkeletonProps) {
  return (
    <div
      className={cn('bg-card rounded-2xl overflow-hidden border border-border/50', className)}
      {...props}
    >
      {/* Cover image placeholder */}
      <Skeleton width="100%" height={140} variant="rectangular" className="rounded-t-2xl" />

      {/* Content */}
      <div className="p-4 space-y-3">
        <Skeleton width="80%" height={20} />
        <TextSkeleton lines={2} />

        {showProgress && (
          <div className="space-y-2">
            <div className="flex justify-between">
              <Skeleton width={60} height={12} />
              <Skeleton width={40} height={12} />
            </div>
            <Skeleton width="100%" height={6} variant="rectangular" className="rounded-full" />
          </div>
        )}

        {/* Metadata */}
        <div className="flex gap-2">
          <Skeleton width={50} height={20} variant="rectangular" className="rounded-full" />
          <Skeleton width={60} height={20} variant="rectangular" className="rounded-full" />
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   Grid Skeleton
   ============================================================ */

export interface GridSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  columns?: number;
  count?: number;
}

export function GridSkeleton({
  columns = 2,
  count = 4,
  className,
  ...props
}: GridSkeletonProps) {
  return (
    <div
      className={cn('grid gap-4', className)}
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      {...props}
    >
      {Array.from({ length: count }).map((_, i) => (
        <ProjectCardSkeleton key={i} />
      ))}
    </div>
  );
}

/* ============================================================
   Typing Indicator Skeleton (for chat)
   ============================================================ */

export function TypingSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex w-full mb-4', className)} {...props}>
      <div className="flex gap-3">
        <div className="shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-primary-foreground/40 animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-primary-foreground/40 animate-pulse delay-100" />
            <span className="w-2 h-2 rounded-full bg-primary-foreground/40 animate-pulse delay-200" />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   Stats Skeleton (for header stats)
   ============================================================ */

export function StatsSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex gap-2', className)} {...props}>
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton
          key={i}
          width={80}
          height={36}
          variant="rectangular"
          className="rounded-full"
        />
      ))}
    </div>
  );
}

/* ============================================================
   Adaptive Skeleton
   ============================================================ */

export type SkeletonContentType =
  | 'text'
  | 'card'
  | 'chat'
  | 'project'
  | 'stats'
  | 'list';

export interface AdaptiveSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  type: SkeletonContentType;
  count?: number;
  delay?: number; // 延迟显示时间（毫秒）
}

/**
 * 自适应骨架屏
 * 根据内容类型自动选择合适的骨架屏组件
 */
export function AdaptiveSkeleton({
  type,
  count = 1,
  delay = 0,
  className,
  ...props
}: AdaptiveSkeletonProps) {
  const [show, setShow] = useState(delay === 0);

  useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShow(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  if (!show) {
    return null;
  }

  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return <TextSkeleton lines={count} className={className} {...props} />;
      case 'card':
        return <CardSkeleton lines={count} className={className} {...props} />;
      case 'chat':
        return <ChatSkeleton className={className} {...props} />;
      case 'project':
        return <ProjectCardSkeleton className={className} {...props} />;
      case 'stats':
        return <StatsSkeleton className={className} {...props} />;
      case 'list':
        return (
          <div className={cn('space-y-3', className)} {...props}>
            {Array.from({ length: count }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        );
      default:
        return <Skeleton className={className} {...props} />;
    }
  };

  return renderSkeleton();
}

/* ============================================================
   Delayed Skeleton
   ============================================================ */

export interface DelayedSkeletonProps extends SkeletonProps {
  delay?: number; // 延迟显示时间（毫秒），避免闪烁
  fallback?: React.ReactNode;
}

/**
 * 延迟显示的骨架屏
 * 避免快速加载时的骨架屏闪烁
 */
export function DelayedSkeleton({
  delay = 200,
  fallback = null,
  className,
  ...props
}: DelayedSkeletonProps) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  if (!show) {
    return <>{fallback}</>;
  }

  return <Skeleton className={className} {...props} />;
}

/* ============================================================
   Streaming Text Skeleton
   ============================================================ */

export interface StreamingTextSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  minLines?: number;
  maxLines?: number;
  animate?: boolean;
}

/**
 * 流式文本骨架屏
 * 模拟AI流式输出的加载效果
 */
export function StreamingTextSkeleton({
  minLines = 2,
  maxLines = 6,
  animate = true,
  className,
  ...props
}: StreamingTextSkeletonProps) {
  const [lines, setLines] = useState(minLines);

  useEffect(() => {
    if (!animate) return;

    const interval = setInterval(() => {
      setLines(prev => {
        if (prev >= maxLines) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 300);

    return () => clearInterval(interval);
  }, [animate, minLines, maxLines]);

  return (
    <div className={cn('space-y-2', className)} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '70%' : '100%'}
          height={14}
        />
      ))}
    </div>
  );
}

// 添加useState导入
import { useState, useEffect } from 'react';
