'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ReadingView, ChapterList } from '@/components/novel/reading-view';
import { mockNovels, mockChapters } from '@/lib/mock-data';
import { BottomTabBar, Header } from '@/components/layout/bottom-tab-bar';
import { List } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function NovelPage() {
  const params = useParams();
  const router = useRouter();
  const novelId = params.id as string;

  const novel = mockNovels.find(n => n.id === novelId);
  const chapters = mockChapters[novelId] || [];

  const [currentChapter, setCurrentChapter] = useState(1);
  const [showTableOfContents, setShowTableOfContents] = useState(false);

  if (!novel) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-foreground mb-2">作品不存在</h1>
          <button
            onClick={() => router.push('/')}
            className="text-primary font-medium"
          >
            返回书架
          </button>
        </div>
      </div>
    );
  }

  if (chapters.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">📝</span>
          </div>
          <h1 className="text-xl font-semibold text-foreground mb-2">该作品还没有内容</h1>
          <p className="text-muted-foreground mb-4">去创作页面和AI一起开始写作吧</p>
          <button
            onClick={() => router.push('/chat')}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-2xl font-medium"
          >
            开始创作
          </button>
        </div>
      </div>
    );
  }

  const currentChapterData = chapters[currentChapter - 1];

  const handlePrev = () => {
    if (currentChapter > 1) {
      setCurrentChapter(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleNext = () => {
    if (currentChapter < chapters.length) {
      setCurrentChapter(prev => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  if (showTableOfContents) {
    return (
      <div className="min-h-screen bg-background pb-20">
        <Header
          title="目录"
          subtitle={`${novel.title} · ${chapters.length}章`}
          showBack
          onBack={() => setShowTableOfContents(false)}
        />
        <div className="max-w-2xl mx-auto">
          <ChapterList
            chapters={chapters}
            currentChapter={currentChapter}
            onSelectChapter={setCurrentChapter}
          />
        </div>
        <BottomTabBar />
      </div>
    );
  }

  return (
    <div>
      <ReadingView
        title={novel.title}
        chapterTitle={currentChapterData?.title || `第${currentChapter}章`}
        content={currentChapterData?.content || '暂无内容'}
        currentChapter={currentChapter}
        totalChapters={chapters.length}
        onPrev={handlePrev}
        onNext={handleNext}
        onSettings={() => setShowTableOfContents(true)}
      />
      {/* Floating TOC Button */}
      <button
        onClick={() => setShowTableOfContents(true)}
        className={cn(
          'fixed top-20 right-4 z-40',
          'w-10 h-10 rounded-full',
          'bg-card shadow-md border border-border/50',
          'flex items-center justify-center',
          'touch-hover'
        )}
        aria-label="目录"
      >
        <List className="w-5 h-5 text-foreground" />
      </button>
      <BottomTabBar />
    </div>
  );
}
