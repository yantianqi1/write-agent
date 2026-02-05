'use client';

import Image from 'next/image';
import Link from 'next/link';
import { cn, formatWordCount, formatDate } from '@/lib/utils';
import { TouchableCard } from '@/components/ui/card';
import { Badge, StatusBadge } from '@/components/ui/badge';
import { ReadingProgress } from '@/components/ui/progress';
import type { Novel } from '@/lib/types';

/* ============================================================
   Novel Card Component - iOS Style
   ============================================================ */

export interface NovelCardProps {
  novel: Novel;
  currentChapter?: number;
  showProgress?: boolean;
  variant?: 'grid' | 'list';
}

export function NovelCard({
  novel,
  currentChapter = 0,
  showProgress = false,
  variant = 'grid',
}: NovelCardProps) {
  if (variant === 'list') {
    return <NovelListItem novel={novel} currentChapter={currentChapter} showProgress={showProgress} />;
  }

  return (
    <Link href={`/novel/${novel.id}`} className="block">
      <TouchableCard className="group overflow-hidden p-0">
        {/* Cover Image */}
        <div className="relative aspect-[3/4] bg-muted overflow-hidden">
          {novel.coverImage ? (
            <Image
              src={novel.coverImage}
              alt={novel.title}
              fill
              className="object-cover transition-transform duration-300 group-active:scale-105"
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-accent">
              <span className="text-4xl font-bold text-muted-foreground/30">
                {novel.title.slice(0, 2)}
              </span>
            </div>
          )}
          {/* Status Badge */}
          <div className="absolute top-3 left-3">
            <StatusBadge status={novel.status} />
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="font-semibold text-base text-foreground truncate mb-1">
            {novel.title}
          </h3>
          {novel.description && (
            <p className="text-sm text-muted-foreground text-ellipsis-2 line-clamp-2 mb-3">
              {novel.description}
            </p>
          )}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatWordCount(novel.wordCount)}</span>
            <span>·</span>
            <span>{novel.chapterCount}章</span>
            <span>·</span>
            <span>{formatDate(novel.updatedAt)}</span>
          </div>
          {showProgress && novel.chapterCount > 0 && (
            <div className="mt-3">
              <ReadingProgress current={currentChapter} total={novel.chapterCount} showLabel />
            </div>
          )}
        </div>
      </TouchableCard>
    </Link>
  );
}

/* ============================================================
   Novel List Item - For list view
   ============================================================ */

function NovelListItem({
  novel,
  currentChapter = 0,
  showProgress = false,
}: NovelCardProps) {
  return (
    <Link href={`/novel/${novel.id}`} className="block">
      <TouchableCard className="group">
        <div className="flex gap-4">
          {/* Cover Thumbnail */}
          <div className="relative w-20 h-28 shrink-0 bg-muted rounded-xl overflow-hidden">
            {novel.coverImage ? (
              <Image
                src={novel.coverImage}
                alt={novel.title}
                fill
                className="object-cover"
                sizes="80px"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-accent">
                <span className="text-lg font-bold text-muted-foreground/30">
                  {novel.title.slice(0, 2)}
                </span>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0 flex flex-col justify-between py-1">
            <div>
              <div className="flex items-start justify-between gap-2 mb-1">
                <h3 className="font-semibold text-base text-foreground truncate">
                  {novel.title}
                </h3>
                <StatusBadge status={novel.status} />
              </div>
              {novel.description && (
                <p className="text-sm text-muted-foreground text-ellipsis-2 line-clamp-2">
                  {novel.description}
                </p>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <span>{formatWordCount(novel.wordCount)}</span>
                <span>·</span>
                <span>{novel.chapterCount}章</span>
                <span>·</span>
                <span>{formatDate(novel.updatedAt)}</span>
              </div>
              {showProgress && novel.chapterCount > 0 && (
                <ReadingProgress current={currentChapter} total={novel.chapterCount} />
              )}
            </div>
          </div>
        </div>
      </TouchableCard>
    </Link>
  );
}

/* ============================================================
   Novel Grid Container
   ============================================================ */

export interface NovelGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3;
}

export function NovelGrid({ children, columns = 2 }: NovelGridProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
    3: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5',
  };

  return (
    <div className={cn('grid gap-4', gridCols[columns])}>
      {children}
    </div>
  );
}
