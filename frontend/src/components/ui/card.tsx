import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

/* ============================================================
   Card Component - iOS Style
   ============================================================ */

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-3xl bg-card p-5 shadow-sm',
        'dark:shadow-none dark:border dark:border-border',
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col gap-1.5', className)} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-lg font-semibold leading-tight tracking-tight text-card-foreground', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-center gap-3 pt-4', className)} {...props} />
  )
);
CardFooter.displayName = 'CardFooter';

/* ============================================================
   Touchable Card - With tap feedback
   ============================================================ */

export interface TouchableCardProps extends HTMLAttributes<HTMLDivElement> {
  href?: string;
  onClick?: () => void;
}

export const TouchableCard = forwardRef<HTMLDivElement, TouchableCardProps>(
  ({ className, children, href, onClick, ...props }, ref) => {
    const Component = href ? 'a' : 'div';

    return (
      <Component
        ref={ref as any}
        href={href}
        className={cn(
          'block rounded-3xl bg-card p-4 shadow-sm active:scale-98 transition-transform duration-150',
          'cursor-pointer',
          'dark:shadow-none dark:border dark:border-border',
          className
        )}
        onClick={onClick}
        {...(props as any)}
      >
        {children}
      </Component>
    );
  }
);

TouchableCard.displayName = 'TouchableCard';
