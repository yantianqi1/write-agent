'use client';

import { useState, useEffect } from 'react';
import { BottomTabBar, FloatingActionButton, Header } from '@/components/layout/bottom-tab-bar';
import { NovelCard, NovelGrid } from '@/components/novel/novel-card';
import { Input } from '@/components/ui/input';
import { Search, BookOpen, Clock, TrendingUp, Loader2 } from 'lucide-react';
import { api, type ProjectInfo } from '@/lib/api';
import { cn, formatWordCount } from '@/lib/utils';
import type { Novel } from '@/lib/types';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'draft' | 'in_progress' | 'completed'>('all');
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setIsLoading(true);
      const data = await api.projects.listProjects();
      setProjects(data);
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to load projects:', error);
      setIsConnected(false);
      // 使用mock数据作为fallback
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  }

  // 过滤项目
  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || project.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  // 转换为Novel类型
  const novels: Novel[] = filteredProjects.map(project => ({
    id: project.id,
    title: project.title,
    description: project.description,
    createdAt: new Date(project.created_at),
    updatedAt: new Date(project.updated_at),
    wordCount: project.word_count,
    chapterCount: project.chapter_count,
    status: project.status === 'draft' ? 'draft' : project.status === 'in_progress' ? 'in_progress' : 'completed',
  }));

  const stats = {
    total: projects.length,
    reading: projects.filter(p => p.status === 'in_progress').length,
    completed: projects.filter(p => p.status === 'completed').length,
    totalWords: projects.reduce((sum, p) => sum + p.word_count, 0),
  };

  return (
    <div className="min-h-screen pb-32">
      <Header
        title="我的书架"
        subtitle={isConnected ? `${stats.total}部作品 · ${(stats.totalWords / 10000).toFixed(1)}万字` : '未连接到API'}
      />

      {/* Search Bar */}
      <div className="px-4 py-3 sticky top-14 z-20 glass">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="搜索作品..."
            className="pl-11 h-10 rounded-xl"
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="px-4 py-3">
        <div className="flex gap-2 overflow-x-auto scrollbar-hide">
          <button
            onClick={() => setFilterStatus('all')}
            className={cn(
              'shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors',
              filterStatus === 'all'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground'
            )}
          >
            全部 {stats.total}
          </button>
          <button
            onClick={() => setFilterStatus('in_progress')}
            className={cn(
              'shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors',
              filterStatus === 'in_progress'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground'
            )}
          >
            连载中 {stats.reading}
          </button>
          <button
            onClick={() => setFilterStatus('completed')}
            className={cn(
              'shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors',
              filterStatus === 'completed'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground'
            )}
          >
            已完结 {stats.completed}
          </button>
        </div>
      </div>

      {/* Novel Grid */}
      <div className="px-4">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-muted-foreground animate-spin mb-4" />
            <p className="text-sm text-muted-foreground">加载中...</p>
          </div>
        ) : !isConnected ? (
          <div className="flex flex-col items-center justify-center py-20 text-center px-8">
            <div className="w-16 h-16 rounded-2xl bg-destructive/10 flex items-center justify-center mb-4">
              <span className="text-3xl">⚠️</span>
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              无法连接到后端服务
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              请确保后端API服务已启动 (运行 <code className="bg-muted px-1 rounded">python src/api/main.py</code>)
            </p>
            <button
              onClick={loadProjects}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-2xl font-medium"
            >
              重试
            </button>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
              <BookOpen className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-1">
              {searchQuery ? '没有找到匹配的作品' : '书架空空如也'}
            </h3>
            <p className="text-sm text-muted-foreground">
              {searchQuery ? '试试其他关键词' : '点击右下角按钮开始创作吧'}
            </p>
          </div>
        ) : (
          <NovelGrid columns={2}>
            {novels.map(novel => (
              <NovelCard
                key={novel.id}
                novel={novel}
                showProgress={novel.status === 'in_progress'}
                currentChapter={Math.floor(Math.random() * novel.chapterCount) + 1}
              />
            ))}
          </NovelGrid>
        )}
      </div>

      {/* Recent Activity Section - only show when connected and has data */}
      {isConnected && !isLoading && novels.length > 0 && searchQuery === '' && (
        <div className="px-4 mt-8">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">最近阅读</h2>
          </div>
          <div className="space-y-3">
            {novels.slice(0, 2).map(novel => (
              <a
                key={novel.id}
                href={`/novel/${novel.id}`}
                className="block bg-card rounded-2xl p-4 active:scale-98 transition-transform duration-150"
              >
                <div className="flex gap-3">
                  <div className="w-12 h-16 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <span className="text-lg font-bold text-muted-foreground/40">
                      {novel.title.slice(0, 2)}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-foreground truncate">{novel.title}</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      读至第{Math.floor(Math.random() * novel.chapterCount) + 1}章 · 2小时前
                    </p>
                  </div>
                  <TrendingUp className="w-4 h-4 text-primary shrink-0 self-center" />
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      <FloatingActionButton onClick={() => {}} />
      <BottomTabBar />
    </div>
  );
}
