import { useEffect } from "react";

export function useDebouncedEffect(
  cb: () => void,
  deps: any[] = [],
  delay: number = 300
) {
  useEffect(() => {
    const handler = setTimeout(() => {
      cb();
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [...(deps || []), delay]);
}
