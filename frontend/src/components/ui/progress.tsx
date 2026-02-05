import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

/* ============================================================
   Progress Bar Component - iOS Style
   ============================================================ */

export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

export const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value, max = 100, size = 'md', color = 'primary', ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    const sizes = {
      sm: 'h-1.5',
      md: 'h-2',
      lg: 'h-3',
    };

    const colors = {
      primary: 'bg-primary',
      success: 'bg-success',
      warning: 'bg-warning',
      danger: 'bg-destructive',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative w-full overflow-hidden rounded-full bg-muted',
          sizes[size],
          className
        )}
        {...props}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300 ease-out',
            colors[color]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  }
);

Progress.displayName = 'Progress';

/* ============================================================
   Reading Progress Component
   ============================================================ */

export interface ReadingProgressProps extends HTMLAttributes<HTMLDivElement> {
  current: number;
  total: number;
  showLabel?: boolean;
}

export const ReadingProgress = forwardRef<HTMLDivElement, ReadingProgressProps>(
  ({ className, current, total, showLabel = false, ...props }, ref) => {
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

    return (
      <div ref={ref} className={cn('flex items-center gap-3', className)} {...props}>
        {showLabel && (
          <span className="text-xs text-muted-foreground tabular-nums">
            {current}/{total}
          </span>
        )}
        <div className="flex-1">
          <Progress value={percentage} size="sm" />
        </div>
        {showLabel && (
          <span className="text-xs text-muted-foreground tabular-nums w-8 text-right">
            {percentage}%
          </span>
        )}
      </div>
    );
  }
);

ReadingProgress.displayName = 'ReadingProgress';
