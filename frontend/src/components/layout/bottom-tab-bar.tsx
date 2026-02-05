'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  BookOpen,
  MessageSquare,
  Settings,
  Plus,
} from 'lucide-react';

/* ============================================================
   Bottom Tab Bar - iOS Style Mobile Navigation
   ============================================================ */

export interface TabItem {
  id: string;
  label: string;
  icon: typeof BookOpen;
  href: string;
  badge?: number;
}

const tabs: TabItem[] = [
  { id: 'library', label: '书架', icon: BookOpen, href: '/' },
  { id: 'chat', label: '创作', icon: MessageSquare, href: '/chat' },
  { id: 'settings', label: '设置', icon: Settings, href: '/settings' },
];

export function BottomTabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 safe-bottom">
      {/* Glass effect background */}
      <div className="glass border-t border-border/20">
        <div className="flex items-center justify-around h-16 px-2">
          {tabs.map((tab) => {
            const isActive = pathname === tab.href;
            const Icon = tab.icon;

            return (
              <Link
                key={tab.id}
                href={tab.href}
                className={cn(
                  'flex flex-col items-center justify-center gap-1 min-w-0 flex-1 py-2 px-1 rounded-2xl',
                  'transition-all duration-200',
                  'touch-hover'
                )}
              >
                <div className="relative">
                  <Icon
                    className={cn(
                      'w-6 h-6 transition-colors',
                      isActive ? 'text-primary' : 'text-muted-foreground'
                    )}
                  />
                  {tab.badge && tab.badge > 0 && (
                    <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive text-[10px] text-white flex items-center justify-center font-medium">
                      {tab.badge > 9 ? '9+' : tab.badge}
                    </span>
                  )}
                </div>
                <span
                  className={cn(
                    'text-[11px] font-medium truncate w-full text-center',
                    isActive ? 'text-primary' : 'text-muted-foreground'
                  )}
                >
                  {tab.label}
                </span>
              </Link>
            );
          })}
        </div>
        {/* Home indicator for iOS */}
        <div className="flex justify-center pb-2">
          <div className="w-32 h-1 bg-foreground/20 rounded-full" />
        </div>
      </div>
    </nav>
  );
}

/* ============================================================
   Floating Action Button - For creating new novel
   ============================================================ */

export interface FloatingActionButtonProps {
  onClick: () => void;
  icon?: typeof Plus;
  label?: string;
}

export function FloatingActionButton({
  onClick,
  icon: Icon = Plus,
  label = '新建',
}: FloatingActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'fixed bottom-24 right-4 z-40',
        'flex items-center justify-center gap-2',
        'h-14 px-5 rounded-full',
        'bg-primary text-primary-foreground',
        'shadow-lg shadow-primary/30',
        'font-medium text-base',
        'transition-all duration-200',
        'active:scale-95 active:shadow-md',
        'touch-hover'
      )}
      aria-label={label}
    >
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </button>
  );
}

/* ============================================================
   Header - iOS Style Navigation Header
   ============================================================ */

export interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  showBack?: boolean;
  onBack?: () => void;
  transparent?: boolean;
}

export function Header({
  title,
  subtitle,
  action,
  showBack = false,
  onBack,
  transparent = false,
}: HeaderProps) {
  return (
    <header
      className={cn(
        'sticky top-0 z-30 safe-top',
        !transparent && 'glass border-b border-border/20'
      )}
    >
      <div className="flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {showBack && (
            <button
              onClick={onBack}
              className="flex items-center justify-center w-8 h-8 -ml-2 rounded-full touch-hover"
              aria-label="返回"
            >
              <svg
                className="w-5 h-5 text-foreground"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          )}
          <div className="min-w-0">
            <h1 className="text-base font-semibold text-foreground truncate">
              {title}
            </h1>
            {subtitle && (
              <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
            )}
          </div>
        </div>
        {action && <div className="flex items-center">{action}</div>}
      </div>
    </header>
  );
}
