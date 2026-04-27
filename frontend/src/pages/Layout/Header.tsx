import { User, Globe, LogIn, UserPlus, Sparkles, Shield } from "lucide-react"
import { memo, useState, useEffect, useCallback } from "react";
import { NavLink } from "react-router";
import { Button, Dropdown, message } from "antd"
import type { MenuProps } from 'antd'
import { LoginDialog } from "./LoginDialog"
import { SignupDialog } from "./SignupDialog"
import { post, get } from "@/utils/request.ts";
import { getCachedHomePageUrl, setCachedHomePageUrl } from "@/utils/systemParam";
import { getHomePageUrl } from "@/utils/systemParam";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n";

interface UserResponse {
  username: string;
  email?: string;
  groupId?: string;
  authenticated: boolean;
  authMode: 'SSO' | 'JWT' | 'NONE';
  requireLogin?: boolean;  // 是否强制要求登录（由 DATAMATE_JWT_ENABLE 控制）
}

function loginUsingPost(data: any) {
  return post("/api/user/login", data);
}

function signupUsingPost(data: any) {
  return post("/api/user/signup", data);
}

function getCurrentUser() {
  return get<UserResponse>("/api/user/me");
}

// ME 登录 URL（根据实际环境修改）
const ME_LOGIN_URL = import.meta.env.VITE_ME_LOGIN_URL || 'https://modelengine.com/login';
const OMS_LOGOUT_URL = import.meta.env.VITE_OMS_LOGOUT_URL || 'https://oms-service/logout';

export function Header() {
  const { t } = useTranslation();
  const [loginOpen, setLoginOpen] = useState(false)
  const [signupOpen, setSignupOpen] = useState(false)
  const [loading, setLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [authMode, setAuthMode] = useState<'SSO' | 'JWT' | 'NONE'>('NONE');
  const [userLoading, setUserLoading] = useState(true);

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      const response = await loginUsingPost(values);
      // Store the token in localStorage
      localStorage.setItem('session', JSON.stringify(response.data));
      message.success(t('user.messages.loginSuccess'));
      setLoginOpen(false);
      // Optionally refresh the page or update the UI
      window.location.reload();
    } catch (error) {
      console.error('Login error:', error);
      message.error(t('user.messages.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (values: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error(t('user.messages.passwordMismatch'));
      return;
    }

    try {
      setLoading(true);
      const { username, email, password } = values;
      const response = await signupUsingPost({ username, email, password });

      message.success(t('user.messages.signupSuccess'));
      localStorage.setItem('session', JSON.stringify(response.data));
      setSignupOpen(false);
    } catch (error) {
      console.error('Registration error:', error);
      message.error(t('user.messages.signupFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    if (authMode === 'SSO') {
      // SSO 模式：检查是否配置了有效的登出 URL
      const logoutUrl = OMS_LOGOUT_URL;

      // 如果配置的是默认值（内部 service 名称），只清除本地状态
      if (logoutUrl.includes('oms-service') || logoutUrl.includes('localhost')) {
        console.warn('OMS logout URL not configured or using internal address, skipping redirect');
        setCurrentUser(null);
        setAuthMode('NONE');
        message.success(t('user.messages.logoutSuccess'));
        window.location.reload();
      } else {
        // 使用配置的登出 URL
        window.location.href = `${logoutUrl}?redirect=${encodeURIComponent(window.location.href)}`;
      }
    } else {
      // JWT 模式：清除本地 session
      localStorage.removeItem('session');
      setCurrentUser(null);
      setAuthMode('NONE');
      message.success(t('user.messages.logoutSuccess'));
      window.location.reload();
    }
  };

  const openLoginDialog = () => {
    setLoginOpen(true);
  };

  const openSignupDialog = () => {
    setSignupOpen(true);
  };

  const handleHomeClick = useCallback((e: React.MouseEvent) => {
    const homeUrl = getCachedHomePageUrl();
    if (homeUrl) {
      e.preventDefault();
      window.location.href = homeUrl;
    }
  }, []);

  // 已登录时后台刷新缓存，保持与后端同步
  useEffect(() => {
    getHomePageUrl().then(url => setCachedHomePageUrl(url)).catch(() => {});
  }, []);

  // 检测是否在 ME 环境
  const isSSOAvailable = () => {
    const hostname = window.location.hostname;
    // 通过域名或注入的全局变量判断
    return hostname.includes('modelengine') ||
           hostname.includes('me-platform') ||
           (window as any).__ME_ENV__ === true;
  };

  // 获取当前用户信息（支持双模式）
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await getCurrentUser();
        if (response.data) {
          setCurrentUser(response.data);
          setAuthMode(response.data.authMode);

          // 如果未登录，根据 requireLogin 决定是否弹出登录框
          if (!response.data.authenticated) {
            if (response.data.requireLogin) {
              // 强制要求登录：弹出登录框
              window.dispatchEvent(new CustomEvent('show-login'));
            }
            // 不强制登录：允许匿名访问
          }
        }
      } catch (error) {
        console.error('Failed to fetch current user:', error);
        // 请求失败时，保持未登录状态
      } finally {
        setUserLoading(false);
      }
    };

    fetchCurrentUser();
  }, []);

  const languageMenuItems: MenuProps['items'] = [
    {
      key: 'zh',
      label: t('header.simplifiedChinese'),
      onClick: () => {
        i18n.changeLanguage('zh');
        localStorage.setItem('language', 'zh');
      },
    },
    {
      key: 'en',
      label: t('header.english'),
      onClick: () => {
        i18n.changeLanguage('en');
        localStorage.setItem('language', 'en');
      },
    }
  ]

  const userDropdownItems: MenuProps['items'] = currentUser?.authenticated
    ? [
        {
          key: 'profile',
          label: (
            <div className="flex flex-col">
              <span className="font-medium">{currentUser.username}</span>
              <span className="text-xs text-gray-500">
                {authMode === 'SSO' ? (
                  <span className="flex items-center gap-1">
                    <Shield className="h-3 w-3" />
                    {t('user.authMode.sso')}
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    {t('user.authMode.jwt')}
                  </span>
                )}
              </span>
            </div>
          ),
        },
        currentUser.groupId && {
          key: 'groupId',
          label: `${t('user.group')}: ${currentUser.groupId}`,
          disabled: true,
        },
        currentUser.email && {
          key: 'email',
          label: currentUser.email,
          disabled: true,
        },
        // 只有 JWT 模式才显示退出登录按钮
        ...(authMode !== 'SSO' ? [
          {
            type: 'divider',
          },
          {
            key: 'logout',
            label: t('user.actions.logout'),
            icon: <LogIn className="h-4 w-4" />,
            onClick: handleLogout,
          },
        ] : []),
      ]
    : [
      {
        key: 'login',
        label: authMode === 'SSO' || isSSOAvailable()
          ? t('user.actions.gotoLogin')
          : t('user.actions.login'),
        icon: <LogIn className="h-4 w-4" />,
        onClick: () => {
          if (authMode === 'SSO' || isSSOAvailable()) {
            // SSO 模式：跳转到 ME 登录
            window.location.href = `${ME_LOGIN_URL}?redirect=${encodeURIComponent(window.location.href)}`;
          } else {
            // JWT 模式：显示登录对话框
            setLoginOpen(true);
          }
        },
      },
      {
        type: 'divider',
      },
      {
        key: 'register',
        label: t('user.actions.register'),
        icon: <UserPlus className="h-4 w-4" />,
        onClick: () => {
          if (authMode === 'SSO' || isSSOAvailable()) {
            message.info(t('user.messages.useSSO'));
          } else {
            setSignupOpen(true);
          }
        },
      },
    ];

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white">
        <div className="flex h-14 items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <NavLink to="/" onClick={handleHomeClick} className="flex items-center gap-2 cursor-pointer">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold text-gray-900">DataMate</span>
              </NavLink>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Dropdown
              menu={{ items: languageMenuItems }}
              placement="bottomRight"
            >
              <Button type="text" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                <span>{i18n.language === 'zh' ? t('header.simplifiedChinese') : t('header.english')}</span>
              </Button>
            </Dropdown>

            <Dropdown
              menu={{ items: userDropdownItems }}
              placement="bottomRight"
              overlayClassName="w-40"
            >
              <Button type="text" icon={<User className="h-4 w-4" />} loading={userLoading}>
                {currentUser?.authenticated && !userLoading && (
                  <span className="ml-1">{currentUser.username}</span>
                )}
              </Button>
            </Dropdown>
          </div>
        </div>
      </header>

      <LoginDialog 
        open={loginOpen} 
        onOpenChange={setLoginOpen} 
        onLogin={handleLogin} 
        loading={loading}
        onSignupClick={openSignupDialog}
      />
      <SignupDialog 
        open={signupOpen} 
        onOpenChange={setSignupOpen} 
        onSignup={handleSignup} 
        loading={loading}
        onLoginClick={openLoginDialog}
      />
    </>
  )
}

export default memo(Header);