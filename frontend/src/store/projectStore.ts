/**
 * Project Store
 *
 * 管理项目状态的Zustand store
 * 使用 immer 中间件优化不可变更新，添加选择器防止不必要的重渲染
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

import type { ProjectInfo, ChapterInfo, ChapterContent } from '@/lib/api';
import { api } from '@/lib/api';

interface ProjectState {
  // 状态数据
  projects: ProjectInfo[];
  currentProject: ProjectInfo | null;
  chapters: Record<string, ChapterInfo[]>; // projectId -> chapters
  currentChapter: ChapterContent | null;

  // 加载状态
  isLoading: boolean;
  error: string | null;

  // 离线状态
  isOnline: boolean;

  // 操作方法
  fetchProjects: () => Promise<void>;
  fetchProject: (projectId: string) => Promise<ProjectInfo | null>;
  createProject: (data: { title: string; description?: string; genre?: string }) => Promise<ProjectInfo | null>;
  updateProject: (projectId: string, data: Partial<ProjectInfo>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  setCurrentProject: (project: ProjectInfo | null) => void;

  // 章节操作
  fetchChapters: (projectId: string) => Promise<ChapterInfo[]>;
  fetchChapter: (projectId: string, chapterId: string) => Promise<ChapterContent | null>;
  setCurrentChapter: (chapter: ChapterContent | null) => void;

  // 清除错误
  clearError: () => void;

  // 离线检测
  checkOnlineStatus: () => void;
}

export const useProjectStore = create<ProjectState>()(
  immer((set, get) => ({
    // 初始状态
    projects: [],
    currentProject: null,
    chapters: {},
    currentChapter: null,
    isLoading: false,
    error: null,
    isOnline: true,  // 默认在线，让 API 调用决定实际状态

    // 检查在线状态
    checkOnlineStatus: () => {
      const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
      set((state) => {
        state.isOnline = isOnline;
      });
    },

    // 获取所有项目
    fetchProjects: async () => {
      console.log('[ProjectStore] fetchProjects called');
      set((state) => {
        state.isLoading = true;
        state.error = null;
      });
      try {
        console.log('[ProjectStore] Calling api.projects.listProjects...');
        const projects = await api.projects.listProjects();
        console.log('[ProjectStore] Got projects:', projects.length);
        set((state) => {
          state.projects = projects;
          state.isLoading = false;
        });
        console.log('[ProjectStore] State updated');
      } catch (error) {
        console.error('[ProjectStore] Error:', error);
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to fetch projects';
          state.isLoading = false;
        });
        throw error; // 重新抛出错误以便页面可以处理
      }
    },

    // 获取单个项目
    fetchProject: async (projectId: string) => {
      // 先检查本地缓存
      const state = get();
      const cached = state.projects.find(p => p.id === projectId);
      if (cached) {
        set((state) => {
          state.currentProject = cached;
        });
        return cached;
      }

      if (!state.isOnline) {
        set((state) => {
          state.error = 'Offline mode: project not in cache';
        });
        return null;
      }

      set((state) => {
        state.isLoading = true;
        state.error = null;
      });
      try {
        const project = await api.projects.getProject(projectId);
        set((state) => {
          state.currentProject = project;
          state.isLoading = false;
        });
        return project;
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to fetch project';
          state.isLoading = false;
        });
        return null;
      }
    },

    // 创建项目（乐观更新）
    createProject: async (data) => {
      const tempId = `temp-${Date.now()}`;
      const tempProject: ProjectInfo = {
        id: tempId,
        title: data.title,
        description: data.description,
        genre: data.genre,
        status: 'draft',
        created_at: new Date(),
        updated_at: new Date(),
        word_count: 0,
        chapter_count: 0,
      };

      // 乐观更新
      set((state) => {
        state.projects.push(tempProject);
        state.isLoading = false;
      });

      try {
        const project = await api.projects.createProject(data);
        // 替换临时项目
        set((state) => {
          const index = state.projects.findIndex(p => p.id === tempId);
          if (index !== -1) {
            state.projects[index] = project;
          }
        });
        return project;
      } catch (error) {
        // 回滚
        set((state) => {
          state.projects = state.projects.filter(p => p.id !== tempId);
          state.error = error instanceof Error ? error.message : 'Failed to create project';
          state.isLoading = false;
        });
        return null;
      }
    },

    // 更新项目（乐观更新）
    updateProject: async (projectId, data) => {
      const state = get();
      const previousProject = state.projects.find(p => p.id === projectId);
      const previousCurrent = state.currentProject;

      // 乐观更新
      if (previousProject) {
        set((state) => {
          // 更新项目列表中的项目
          const project = state.projects.find(p => p.id === projectId);
          if (project) {
            Object.assign(project, data);
          }
          // 更新当前项目
          if (state.currentProject?.id === projectId) {
            Object.assign(state.currentProject, data);
          }
        });
      }

      try {
        const updated = await api.projects.updateProject(projectId, data);
        set((state) => {
          // 使用服务器返回的数据更新
          const project = state.projects.find(p => p.id === projectId);
          if (project) {
            Object.assign(project, updated);
          }
          if (state.currentProject?.id === projectId) {
            Object.assign(state.currentProject, updated);
          }
          state.isLoading = false;
        });
      } catch (error) {
        // 回滚
        set((state) => {
          const project = state.projects.find(p => p.id === projectId);
          if (project && previousProject) {
            Object.assign(project, previousProject);
          }
          if (state.currentProject?.id === projectId && previousCurrent) {
            state.currentProject = previousCurrent;
          }
          state.error = error instanceof Error ? error.message : 'Failed to update project';
          state.isLoading = false;
        });
      }
    },

    // 删除项目（乐观更新）
    deleteProject: async (projectId) => {
      const state = get();
      const previousProjects = [...state.projects];
      const previousCurrent = state.currentProject;
      const previousChapters = { ...state.chapters };

      // 乐观更新
      set((draft) => {
        draft.projects = draft.projects.filter((p) => p.id !== projectId);
        if (draft.currentProject?.id === projectId) {
          draft.currentProject = null;
        }
        draft.chapters[projectId] = [];
      });

      try {
        await api.projects.deleteProject(projectId);
      } catch (error) {
        // 回滚
        set((state) => {
          state.projects = previousProjects;
          state.currentProject = previousCurrent;
          state.chapters = previousChapters;
          state.error = error instanceof Error ? error.message : 'Failed to delete project';
          state.isLoading = false;
        });
      }
    },

    // 设置当前项目
    setCurrentProject: (project) => {
      set((state) => {
        state.currentProject = project;
      });
    },

    // 获取项目章节
    fetchChapters: async (projectId) => {
      set((state) => {
        state.isLoading = true;
        state.error = null;
      });
      try {
        const chapters = await api.projects.listChapters(projectId);
        set((state) => {
          state.chapters[projectId] = chapters;
          state.isLoading = false;
        });
        return chapters;
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to fetch chapters';
          state.isLoading = false;
        });
        return [];
      }
    },

    // 获取章节内容
    fetchChapter: async (projectId, chapterId) => {
      set((state) => {
        state.isLoading = true;
        state.error = null;
      });
      try {
        const chapter = await api.projects.getChapter(projectId, chapterId);
        set((state) => {
          state.currentChapter = chapter;
          state.isLoading = false;
        });
        return chapter;
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Failed to fetch chapter';
          state.isLoading = false;
        });
        return null;
      }
    },

    // 设置当前章节
    setCurrentChapter: (chapter) => {
      set((state) => {
        state.currentChapter = chapter;
      });
    },

    // 清除错误
    clearError: () => {
      set((state) => {
        state.error = null;
      });
    },
  }))
);

/* ============================================================
   选择器 - 防止不必要的重渲染
   ============================================================ */

/**
 * 获取所有项目
 */
export const selectProjects = (state: ProjectState) => state.projects;

/**
 * 获取当前项目
 */
export const selectCurrentProject = (state: ProjectState) => state.currentProject;

/**
 * 获取项目加载状态
 */
export const selectProjectsLoading = (state: ProjectState) => state.isLoading;

/**
 * 获取项目错误信息
 */
export const selectProjectsError = (state: ProjectState) => state.error;

/**
 * 根据ID获取项目
 */
export const selectProjectById = (projectId: string) => (state: ProjectState) => {
  return state.projects.find(p => p.id === projectId) || null;
};

/**
 * 获取项目的章节列表
 */
export const selectChaptersByProjectId = (projectId: string) => (state: ProjectState) => {
  return state.chapters[projectId] || [];
};

/**
 * Hook: 使用项目列表（带选择器优化）
 */
export const useProjects = () => useProjectStore(selectProjects);

/**
 * Hook: 使用当前项目（带选择器优化）
 */
export const useCurrentProject = () => useProjectStore(selectCurrentProject);

/**
 * Hook: 使用项目加载状态（带选择器优化）
 */
export const useProjectsLoading = () => useProjectStore(selectProjectsLoading);

// 监听在线状态
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => useProjectStore.getState().checkOnlineStatus());
  window.addEventListener('offline', () => useProjectStore.getState().checkOnlineStatus());
}
