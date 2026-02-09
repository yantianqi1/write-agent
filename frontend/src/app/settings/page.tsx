'use client';

import { BottomTabBar, Header } from '@/components/layout/bottom-tab-bar';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Moon, Sun, Bell, Lock, Info, LogOut, Languages, type LucideIcon } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useI18n, locales, type Locale } from '@/lib/i18n';

type SettingItemType = 'toggle' | 'chevron';

interface SettingItem {
  icon: LucideIcon;
  label: string;
  value?: string;
  action?: () => void;
  type: SettingItemType;
  checked?: boolean;
}

export default function SettingsPage() {
  const router = useRouter();
  const { locale, setLocale, t } = useI18n();
  const [darkMode, setDarkMode] = useState(false);
  const [isChangingLocale, setIsChangingLocale] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  const settingsSections: { title: string; items: SettingItem[] }[] = [
    {
      title: t.settings?.language || '语言',
      items: [
        {
          icon: Languages,
          label: t.settings?.language || '语言',
          value: locales.find(l => l.code === locale)?.nativeName || '简体中文',
          action: async () => {
            setIsChangingLocale(true);
            const currentIndex = locales.findIndex(l => l.code === locale);
            const nextIndex = (currentIndex + 1) % locales.length;
            await setLocale(locales[nextIndex].code);
            setIsChangingLocale(false);
          },
          type: 'chevron',
        },
      ],
    },
    {
      title: t.settings?.theme || '外观',
      items: [
        {
          icon: darkMode ? Sun : Moon,
          label: '深色模式',
          value: darkMode ? '开启' : '关闭',
          action: toggleDarkMode,
          type: 'toggle',
          checked: darkMode,
        },
      ],
    },
    {
      title: '通知',
      items: [
        {
          icon: Bell,
          label: '推送通知',
          value: '已开启',
          type: 'chevron',
        },
        {
          icon: Bell,
          label: '创作完成提醒',
          value: '已开启',
          type: 'chevron',
        },
      ],
    },
    {
      title: '隐私与安全',
      items: [
        {
          icon: Lock,
          label: '修改密码',
          type: 'chevron',
        },
        {
          icon: Lock,
          label: '隐私设置',
          type: 'chevron',
        },
      ],
    },
    {
      title: '关于',
      items: [
        {
          icon: Info,
          label: '关于 WriteAgent',
          value: 'v1.0.0',
          type: 'chevron',
        },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-background pb-32">
      <Header title={t.settings?.title || '设置'} showBack onBack={() => router.push('/')} />

      <div className="p-4 space-y-6">
        {/* Profile Card */}
        <Card className="p-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
              <span className="text-2xl font-bold text-primary">用</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">用户名</h3>
              <p className="text-sm text-muted-foreground">user@example.com</p>
            </div>
            <Button size="sm" variant="ghost">
              编辑
            </Button>
          </div>
        </Card>

        {/* Settings Sections */}
        {settingsSections.map((section, index) => (
          <div key={index}>
            <h3 className="text-sm font-medium text-muted-foreground mb-2 px-1">
              {section.title}
            </h3>
            <div className="bg-card rounded-3xl overflow-hidden divide-y divide-border/50">
              {section.items.map((item, itemIndex) => (
                <button
                  key={itemIndex}
                  onClick={item.action}
                  className={cn(
                    'w-full flex items-center gap-3 p-4',
                    'active:bg-muted transition-colors duration-150',
                    'touch-hover'
                  )}
                >
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                    <item.icon className="w-4 h-4 text-foreground" />
                  </div>
                  <span className="flex-1 text-left text-foreground">{item.label}</span>
                  {item.type === 'toggle' ? (
                    <div
                      className={cn(
                        'w-12 h-7 rounded-full transition-colors duration-200',
                        item.checked ? 'bg-primary' : 'bg-muted'
                      )}
                    >
                      <div
                        className={cn(
                          'w-6 h-6 rounded-full bg-white shadow-sm transition-transform duration-200',
                          item.checked ? 'translate-x-6' : 'translate-x-0.5'
                        )}
                      />
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      {item.value && <span className="text-sm">{item.value}</span>}
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        ))}

        {/* Logout Button */}
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 h-14 px-4 rounded-2xl"
          onClick={() => {
            localStorage.removeItem('writeagent_jwt_token');
            localStorage.removeItem('writeagent_user_info');
            router.push('/login');
          }}
        >
          <LogOut className="w-5 h-5 text-destructive" />
          <span className="text-destructive">{t.auth?.logout || '退出登录'}</span>
        </Button>

        {/* Version Info */}
        <p className="text-center text-xs text-muted-foreground py-4">
          WriteAgent v1.0.0 · Made with AI
        </p>
      </div>

      <BottomTabBar />
    </div>
  );
}
