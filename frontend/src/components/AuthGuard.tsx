import { useState, useEffect, useCallback } from "react";
import { message } from "antd";
import { LoginDialog } from "@/pages/Layout/LoginDialog";
import { SignupDialog } from "@/pages/Layout/SignupDialog";
import { post } from "@/utils/request";
import { useTranslation } from "react-i18next";

function loginUsingPost(data: { username: string; password: string }) {
  return post("/api/user/login", data);
}

function signupUsingPost(data: { username: string; email: string; password: string }) {
  return post("/api/user/signup", data);
}

export function AuthGuard() {
  const { t } = useTranslation();
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const openLoginDialog = useCallback(() => {
    console.log('[AuthGuard] openLoginDialog called, setting loginOpen to true');
    setLoginOpen(true);
  }, []);

  const openSignupDialog = useCallback(() => {
    console.log('[AuthGuard] openSignupDialog called');
    setSignupOpen(true);
  }, []);

  useEffect(() => {
    console.log('[AuthGuard] Registering show-login event listener');
    window.addEventListener("show-login", openLoginDialog);
    
    return () => {
      console.log('[AuthGuard] Removing show-login event listener');
      window.removeEventListener("show-login", openLoginDialog);
    };
  }, [openLoginDialog]);

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      const response = await loginUsingPost(values);
      localStorage.setItem("session", JSON.stringify(response.data));
      message.success(t("user.messages.loginSuccess"));
      setLoginOpen(false);
      window.location.reload();
    } catch (error) {
      console.error("Login error:", error);
      message.error(t("user.messages.loginFailed"));
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (values: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error(t("user.messages.passwordMismatch"));
      return;
    }

    try {
      setLoading(true);
      const { username, email, password } = values;
      const response = await signupUsingPost({ username, email, password });
      message.success(t("user.messages.signupSuccess"));
      localStorage.setItem("session", JSON.stringify(response.data));
      setSignupOpen(false);
      window.location.reload();
    } catch (error) {
      console.error("Registration error:", error);
      message.error(t("user.messages.signupFailed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
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
  );
}

export default AuthGuard;
