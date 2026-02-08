/**
 * UI Store
 *
 * 管理UI状态的Zustand store
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface UIState {
  // 主题
  theme: Theme;

  // 侧边栏状态
  sidebarCollapsed: boolean;

  // 底部导航栏当前标签
  currentTab: string;

  // 模态框状态
  modals: {
    createProject: boolean;
    settings: boolean;
  };

  // 通知
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
    timestamp: Date;
  }>;

  // 操作方法
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentTab: (tab: string) => void;
  openModal: (modal: keyof UIState['modals']) => void;
  closeModal: (modal: keyof UIState['modals']) => void;
  addNotification: (notification: {
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
  }) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // 初始状态
      theme: 'system',
      sidebarCollapsed: false,
      currentTab: 'home',
      modals: {
        createProject: false,
        settings: false,
      },
      notifications: [],

      // 设置主题
      setTheme: (theme) => {
        set({ theme });
        // 应用主题到DOM
        if (typeof window !== 'undefined') {
          const root = document.documentElement;
          if (theme === 'dark') {
            root.classList.add('dark');
          } else if (theme === 'light') {
            root.classList.remove('dark');
          } else {
            // 跟随系统
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
              root.classList.add('dark');
            } else {
              root.classList.remove('dark');
            }
          }
        }
      },

      // 切换侧边栏
      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      // 设置侧边栏状态
      setSidebarCollapsed: (collapsed) => {
        set({ sidebarCollapsed: collapsed });
      },

      // 设置当前标签
      setCurrentTab: (tab) => {
        set({ currentTab: tab });
      },

      // 打开模态框
      openModal: (modal) => {
        set((state) => ({
          modals: { ...state.modals, [modal]: true },
        }));
      },

      // 关闭模态框
      closeModal: (modal) => {
        set((state) => ({
          modals: { ...state.modals, [modal]: false },
        }));
      },

      // 添加通知
      addNotification: (notification) => {
        const id = `notif-${Date.now()}-${Math.random()}`;
        set((state) => ({
          notifications: [
            ...state.notifications,
            { ...notification, id, timestamp: new Date() },
          ],
        }));

        // 自动移除通知
        setTimeout(() => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        }, 5000);
      },

      // 移除通知
      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      },

      // 清除所有通知
      clearNotifications: () => {
        set({ notifications: [] });
      },
    }),
    {
      name: 'ui-storage',
    }
  )
);
