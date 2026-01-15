import { User, Globe, LogIn, UserPlus, Sparkles } from "lucide-react"
import { memo, useState, useEffect } from "react";
import { NavLink } from "react-router";
import { Button, Dropdown, message } from "antd"
import type { MenuProps } from 'antd'
import { LoginDialog } from "./LoginDialog"
import { SignupDialog } from "./SignupDialog"
import { post} from "@/utils/request.ts";

function loginUsingPost(data: any) {
  return post("/api/user/login", data);
}

function signupUsingPost(data: any) {
  return post("/api/user/signup", data);
}

export function Header() {
  const [loginOpen, setLoginOpen] = useState(false)
  const [signupOpen, setSignupOpen] = useState(false)
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      const response = await loginUsingPost(values);
      // Store the token in localStorage
      localStorage.setItem('session', JSON.stringify(response.data));
      message.success('登录成功');
      setLoginOpen(false);
      // Optionally refresh the page or update the UI
      window.location.reload();
    } catch (error) {
      console.error('Login error:', error);
      message.error('登录失败，请稍后重试');
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
      message.error('两次输入的密码不一致');
      return;
    }

    try {
      setLoading(true);
      const { username, email, password } = values;
      const response = await signupUsingPost({ username, email, password });

      message.success('注册成功，已自动登录');
      localStorage.setItem('session', JSON.stringify(response.data));
      setSignupOpen(false);
    } catch (error) {
      console.error('Registration error:', error);
      message.error('注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('session');
    message.success('已退出登录');
    // Refresh the page after logout
    window.location.reload();
  };

  const openLoginDialog = () => {
    setLoginOpen(true);
  };

  const openSignupDialog = () => {
    setSignupOpen(true);
  };

  useEffect(() => {
    window.addEventListener('show-login', openLoginDialog);

    return () => {
      window.removeEventListener('show-login', openLoginDialog);
    };
  }, []);

  const languageMenuItems: MenuProps['items'] = [
    {
      key: 'zh',
      label: '简体中文',
    },
    // {
    //   key: 'en',
    //   label: 'English',
    // }
  ]

  const userDropdownItems: MenuProps['items'] = localStorage.getItem("session")
    ? [
      {
        key: 'profile',
        label: JSON.parse(localStorage.getItem("session") as string).email,
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        label: '退出登录',
        icon: <LogIn className="h-4 w-4" />,
        onClick: handleLogout,
      },
    ]
    : [
      {
        key: 'login',
        label: '登录',
        icon: <LogIn className="h-4 w-4" />,
        onClick: () => setLoginOpen(true),
      },
      {
        type: 'divider',
      },
      {
        key: 'register',
        label: '注册',
        icon: <UserPlus className="h-4 w-4" />,
        onClick: () => setSignupOpen(true),
      },
    ];

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white">
        <div className="flex h-14 items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <NavLink to="/" className="flex items-center gap-2 cursor-pointer">
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
                <span>简体中文</span>
              </Button>
            </Dropdown>

            <Dropdown
              menu={{ items: userDropdownItems }}
              placement="bottomRight"
              overlayClassName="w-40"
            >
              <Button type="text" icon={<User className="h-4 w-4" />}>
                {localStorage.getItem("session") ? (
                  <span className="ml-1">{JSON.parse(localStorage.getItem("session") as string).username}</span>
                ) : null}
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