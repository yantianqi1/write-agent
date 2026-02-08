/**
 * Generation Store
 *
 * 管理内容生成状态的Zustand store
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { GenerationRequest, GenerationResponse } from '@/lib/api';
import { api } from '@/lib/api';

type GenerationStatus = 'idle' | 'generating' | 'completed' | 'failed';

interface GenerationState {
  // 当前生成状态
  status: GenerationStatus;

  // 当前生成任务ID
  currentTaskId: string | null;

  // 最新生成结果
  lastResult: GenerationResponse | null;

  // 进度信息
  progress: number; // 0-100

  // 错误信息
  error: string | null;

  // 操作方法
  generateChapter: (request: GenerationRequest) => Promise<GenerationResponse | null>;
  setStatus: (status: GenerationStatus) => void;
  setProgress: (progress: number) => void;
  reset: () => void;

  // 清除错误
  clearError: () => void;
}

export const useGenerationStore = create<GenerationState>()(
  persist(
    (set, get) => ({
      // 初始状态
      status: 'idle',
      currentTaskId: null,
      lastResult: null,
      progress: 0,
      error: null,

      // 生成章节
      generateChapter: async (request) => {
        set({ status: 'generating', progress: 0, error: null });

        try {
          // 模拟进度更新
          const progressInterval = setInterval(() => {
            const state = get();
            if (state.status === 'generating' && state.progress < 90) {
              set((state) => ({
                progress: Math.min(state.progress + 10, 90),
              }));
            }
          }, 500);

          const response = await api.generation.generateChapter(request);

          clearInterval(progressInterval);

          set({
            status: 'completed',
            progress: 100,
            lastResult: response,
            currentTaskId: response.metadata?.task_id || null,
          });

          return response;
        } catch (error) {
          set({
            status: 'failed',
            error: error instanceof Error ? error.message : 'Generation failed',
          });
          return null;
        }
      },

      // 设置状态
      setStatus: (status) => {
        set({ status });
      },

      // 设置进度
      setProgress: (progress) => {
        set({ progress: Math.min(Math.max(progress, 0), 100) });
      },

      // 重置状态
      reset: () => {
        set({
          status: 'idle',
          currentTaskId: null,
          lastResult: null,
          progress: 0,
          error: null,
        });
      },

      // 清除错误
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'generation-storage',
      partialize: (state) => ({
        lastResult: state.lastResult,
      }),
    }
  )
);
