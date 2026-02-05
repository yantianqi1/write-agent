'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Settings, ChevronLeft, ChevronRight, Minus, Plus } from 'lucide-react';

/* ============================================================
   Reading View Component - iOS Style
   ============================================================ */

export interface ReadingViewProps {
  title: string;
  content: string;
  chapterTitle: string;
  currentChapter: number;
  totalChapters: number;
  onPrev?: () => void;
  onNext?: () => void;
  onSettings?: () => void;
}

export function ReadingView({
  title,
  content,
  chapterTitle,
  currentChapter,
  totalChapters,
  onPrev,
  onNext,
  onSettings,
}: ReadingViewProps) {
  const [fontSize, setFontSize] = useState(16);
  const [lineHeight, setLineHeight] = useState(1.8);
  const [showSettings, setShowSettings] = useState(false);

  const handleFontSizeChange = (delta: number) => {
    setFontSize(prev => Math.min(Math.max(prev + delta, 14), 24));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 glass safe-top">
        <div className="flex items-center justify-between px-4 h-14 border-b border-border/20">
          <button
            className="w-8 h-8 -ml-2 flex items-center justify-center rounded-full touch-hover"
            aria-label="返回"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 min-w-0 mx-4">
            <h1 className="text-sm font-medium text-foreground truncate">{title}</h1>
            <p className="text-xs text-muted-foreground truncate">
              第{currentChapter}章 · {chapterTitle}
            </p>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-8 h-8 -mr-2 flex items-center justify-center rounded-full touch-hover"
            aria-label="设置"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-card border-b border-border animate-slide-down">
          <div className="px-4 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium">字号</span>
              <div className="flex items-center gap-3">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleFontSizeChange(-2)}
                  className="h-8 w-8 p-0 rounded-xl"
                >
                  <Minus className="w-4 h-4" />
                </Button>
                <span className="text-sm tabular-nums w-8 text-center">{fontSize}</span>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleFontSizeChange(2)}
                  className="h-8 w-8 p-0 rounded-xl"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">行距</span>
              <div className="flex gap-2">
                {[1.5, 1.8, 2.0].map(spacing => (
                  <button
                    key={spacing}
                    onClick={() => setLineHeight(spacing)}
                    className={cn(
                      'px-3 py-1.5 text-xs rounded-xl transition-colors',
                      lineHeight === spacing
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-secondary-foreground'
                    )}
                  >
                    {spacing}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <article
        className="max-w-2xl mx-auto px-5 py-8"
        style={{ fontSize: `${fontSize}px`, lineHeight: lineHeight }}
      >
        <h2 className="text-xl font-bold text-foreground mb-6">{chapterTitle}</h2>
        <div className="prose prose-base dark:prose-invert max-w-none">
          {content.split('\n\n').map((paragraph, index) => (
            <p
              key={index}
              className="mb-4 text-foreground leading-relaxed text-justify"
            >
              {paragraph}
            </p>
          ))}
        </div>
      </article>

      {/* Chapter Navigation */}
      <div className="sticky bottom-20 left-0 right-0 z-20 px-4 py-3">
        <div className="max-w-2xl mx-auto flex gap-3">
          <Button
            variant="secondary"
            className="flex-1"
            disabled={currentChapter <= 1}
            onClick={onPrev}
          >
            <ChevronLeft className="w-4 h-4" />
            上一章
          </Button>
          <Button
            variant="secondary"
            className="flex-1"
            disabled={currentChapter >= totalChapters}
            onClick={onNext}
          >
            下一章
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="fixed top-14 left-0 right-0 h-0.5 bg-muted">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${(currentChapter / totalChapters) * 100}%` }}
        />
      </div>
    </div>
  );
}

/* ============================================================
   Chapter List Component
   ============================================================ */

export interface Chapter {
  id: string;
  title: string;
  wordCount: number;
}

export interface ChapterListProps {
  chapters: Chapter[];
  currentChapter: number;
  onSelectChapter: (index: number) => void;
}

export function ChapterList({ chapters, currentChapter, onSelectChapter }: ChapterListProps) {
  return (
    <div className="divide-y divide-border/50">
      {chapters.map((chapter, index) => (
        <button
          key={chapter.id}
          onClick={() => onSelectChapter(index + 1)}
          className={cn(
            'w-full px-4 py-4 flex items-center justify-between',
            'transition-colors duration-150',
            'active:bg-muted',
            currentChapter === index + 1 && 'bg-muted/50'
          )}
        >
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  'text-sm',
                  currentChapter === index + 1 ? 'text-primary font-medium' : 'text-muted-foreground'
                )}
              >
                第{index + 1}章
              </span>
              {currentChapter === index + 1 && (
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </div>
            <p
              className={cn(
                'text-sm truncate mt-0.5',
                currentChapter === index + 1 ? 'text-foreground font-medium' : 'text-foreground'
              )}
            >
              {chapter.title}
            </p>
          </div>
          <span className="text-xs text-muted-foreground ml-4 shrink-0">
            {chapter.wordCount}字
          </span>
        </button>
      ))}
    </div>
  );
}
