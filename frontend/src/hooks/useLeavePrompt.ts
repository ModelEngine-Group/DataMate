import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";

// 自定义hook：页面离开前提示
export function useLeavePrompt(shouldPrompt: boolean) {
  const navigate = useNavigate();
  const [showPrompt, setShowPrompt] = useState(false);
  const [nextPath, setNextPath] = useState<string | null>(null);

  // 浏览器刷新/关闭
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (shouldPrompt) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [shouldPrompt]);

  // 路由切换拦截
  useEffect(() => {
    const unblock = (window as any).__REACT_ROUTER_DOM_HISTORY__?.block?.(
      (tx: any) => {
        if (shouldPrompt) {
          setShowPrompt(true);
          setNextPath(tx.location.pathname);
          return false;
        }
        return true;
      }
    );
    return () => {
      if (unblock) unblock();
    };
  }, [shouldPrompt]);

  const confirmLeave = useCallback(() => {
    setShowPrompt(false);
    if (nextPath) {
      navigate(nextPath, { replace: true });
    }
  }, [nextPath, navigate]);

  return {
    showPrompt,
    setShowPrompt,
    confirmLeave,
  };
}
