import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

/* ============================================================
   Badge Component - iOS Style
   ============================================================ */

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md';
}

export const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const variants = {
      default: 'bg-muted text-muted-foreground',
      primary: 'bg-primary/10 text-primary',
      success: 'bg-success/10 text-success',
      warning: 'bg-warning/10 text-warning',
      danger: 'bg-destructive/10 text-destructive',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-xs',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full font-medium',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

/* ============================================================
   Status Badge - For novel status
   ============================================================ */

export type NovelStatus = 'draft' | 'in_progress' | 'completed';

export interface StatusBadgeProps extends HTMLAttributes<HTMLDivElement> {
  status: NovelStatus;
}

export const StatusBadge = forwardRef<HTMLDivElement, StatusBadgeProps>(
  ({ className, status, ...props }, ref) => {
    const statusConfig: Record<NovelStatus, { label: string; variant: BadgeProps['variant'] }> = {
      draft: { label: '草稿', variant: 'default' },
      in_progress: { label: '连载中', variant: 'primary' },
      completed: { label: '已完结', variant: 'success' },
    };

    const config = statusConfig[status];

    return (
      <Badge ref={ref} variant={config.variant} className={className} {...props}>
        {config.label}
      </Badge>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';
