import { type ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

/* ============================================================
   Button Component - iOS Style
   ============================================================ */

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = [
      'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200',
      'disabled:opacity-40 disabled:cursor-not-allowed',
      'touch-hover',
    ];

    const variants = {
      primary: [
        'bg-primary text-primary-foreground',
        'hover:bg-primary/90',
        'active:scale-98',
        'shadow-md shadow-primary/20',
      ],
      secondary: [
        'bg-secondary text-secondary-foreground',
        'hover:bg-secondary/80',
        'active:scale-98',
      ],
      ghost: [
        'bg-transparent text-foreground',
        'hover:bg-muted',
        'active:scale-98',
      ],
      danger: [
        'bg-destructive text-white',
        'hover:bg-destructive/90',
        'active:scale-98',
        'shadow-md shadow-destructive/20',
      ],
      success: [
        'bg-success text-white',
        'hover:bg-success/90',
        'active:scale-98',
        'shadow-md shadow-success/20',
      ],
    };

    const sizes = {
      sm: 'h-9 px-4 text-sm rounded-xl',
      md: 'h-11 px-5 text-base rounded-2xl',
      lg: 'h-13 px-6 text-lg rounded-2xl',
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            {children && <span>{children}</span>}
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
