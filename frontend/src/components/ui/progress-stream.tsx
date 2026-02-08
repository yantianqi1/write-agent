/**
 * Streaming Progress Components
 *
 * UI components for displaying streaming generation progress
 * with typing indicators and smooth animations.
 */

'use client';

import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

/* ============================================================
   Typing Indicator
   ============================================================ */

export interface TypingIndicatorProps {
  className?: string;
  dotCount?: number;
  speed?: 'slow' | 'normal' | 'fast';
}

export function TypingIndicator({
  className,
  dotCount = 3,
  speed = 'normal',
}: TypingIndicatorProps) {
  const speedClasses = {
    slow: 'duration-500',
    normal: 'duration-300',
    fast: 'duration-150',
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {Array.from({ length: dotCount }).map((_, i) => (
        <span
          key={i}
          className={cn(
            'w-2 h-2 rounded-full bg-primary animate-pulse',
            speedClasses[speed]
          )}
          style={{
            animationDelay: `${i * 150}ms`,
          }}
        />
      ))}
    </div>
  );
}

/* ============================================================
   Streaming Text
   ============================================================ */

export interface StreamingTextProps {
  text: string;
  isStreaming?: boolean;
  className?: string;
  speed?: number; // Characters per frame
}

export function StreamingText({
  text,
  isStreaming = false,
  className,
  speed = 2,
}: StreamingTextProps) {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayText(text);
      setCurrentIndex(text.length);
      return;
    }

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(text.slice(0, currentIndex + speed));
        setCurrentIndex(currentIndex + speed);
      }, 30);

      return () => clearTimeout(timer);
    }
  }, [text, isStreaming, currentIndex, speed]);

  // Reset when text changes completely
  useEffect(() => {
    if (text !== displayText && displayText.length > text.length) {
      setDisplayText('');
      setCurrentIndex(0);
    }
  }, [text, displayText]);

  return (
    <span className={className}>
      {displayText}
      {isStreaming && currentIndex < text.length && (
        <span className="inline-block w-1 h-4 bg-primary animate-pulse ml-0.5" />
      )}
    </span>
  );
}

/* ============================================================
   Progress Bar with Streaming
   ============================================================ */

export interface StreamingProgressBarProps {
  progress: number; // 0-100
  isStreaming?: boolean;
  className?: string;
  showPercentage?: boolean;
  label?: string;
}

export function StreamingProgressBar({
  progress,
  isStreaming = false,
  className,
  showPercentage = false,
  label,
}: StreamingProgressBarProps) {
  const [displayProgress, setDisplayProgress] = useState(0);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayProgress(progress);
      return;
    }

    const timer = setTimeout(() => {
      setDisplayProgress(progress);
    }, 100);

    return () => clearTimeout(timer);
  }, [progress, isStreaming]);

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          {label && <span>{label}</span>}
          {showPercentage && <span>{Math.round(displayProgress)}%</span>}
        </div>
      )}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full bg-primary transition-all duration-300 ease-out',
            isStreaming && 'animate-pulse'
          )}
          style={{ width: `${Math.min(100, Math.max(0, displayProgress))}%` }}
        />
      </div>
    </div>
  );
}

/* ============================================================
   Streaming Card
   ============================================================ */

export interface StreamingCardProps {
  title: string;
  content: string;
  isStreaming?: boolean;
  onStop?: () => void;
  className?: string;
}

export function StreamingCard({
  title,
  content,
  isStreaming = false,
  onStop,
  className,
}: StreamingCardProps) {
  return (
    <div className={cn('bg-card rounded-2xl p-4 border border-border/50', className)}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-foreground">{title}</h3>
        {isStreaming && (
          <div className="flex items-center gap-2">
            <TypingIndicator />
            {onStop && (
              <button
                onClick={onStop}
                className="text-xs text-muted-foreground hover:text-destructive transition-colors"
              >
                停止
              </button>
            )}
          </div>
        )}
      </div>
      <div className="text-sm text-foreground/80 whitespace-pre-wrap">
        {content || (isStreaming && <span className="text-muted-foreground">生成中...</span>)}
      </div>
    </div>
  );
}

/* ============================================================
   Wave Animation (for streaming)
   ============================================================ */

export interface WaveAnimationProps {
  className?: string;
  barCount?: number;
  color?: string;
}

export function WaveAnimation({
  className,
  barCount = 5,
  color = 'hsl(var(--primary))',
}: WaveAnimationProps) {
  return (
    <div className={cn('flex items-center gap-1 h-6', className)}>
      {Array.from({ length: barCount }).map((_, i) => (
        <span
          key={i}
          className="w-1 rounded-full animate-pulse"
          style={{
            backgroundColor: color,
            height: `${40 + Math.random() * 60}%`,
            animationDelay: `${i * 100}ms`,
            animationDuration: `${800 + i * 100}ms`,
          }}
        />
      ))}
    </div>
  );
}

/* ============================================================
   Streaming Status Badge
   ============================================================ */

export type StreamingStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';

export interface StreamingStatusBadgeProps {
  status: StreamingStatus;
  className?: string;
}

export function StreamingStatusBadge({ status, className }: StreamingStatusBadgeProps) {
  const statusConfig = {
    idle: { label: '等待输入', color: 'bg-muted text-muted-foreground' },
    connecting: { label: '连接中...', color: 'bg-yellow-500/20 text-yellow-600' },
    streaming: { label: '生成中', color: 'bg-primary/20 text-primary' },
    completed: { label: '完成', color: 'bg-green-500/20 text-green-600' },
    error: { label: '错误', color: 'bg-destructive/20 text-destructive' },
  };

  const config = statusConfig[status];

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className={cn('px-2 py-1 rounded-full text-xs font-medium', config.color)}>
        {config.label}
      </span>
      {status === 'streaming' && <TypingIndicator dotCount={2} speed="fast" />}
    </div>
  );
}

/* ============================================================
   Animated Cursor
   ============================================================ */

export interface AnimatedCursorProps {
  className?: string;
  color?: string;
}

export function AnimatedCursor({ className, color = 'currentColor' }: AnimatedCursorProps) {
  return (
    <span
      className={cn('inline-block w-0.5 h-4 animate-pulse', className)}
      style={{ backgroundColor: color }}
    />
  );
}
