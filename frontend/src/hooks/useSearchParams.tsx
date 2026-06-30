import { useMemo } from "react";
import { useLocation } from "react-router";

interface AnyObject {
  [key: string]: any;
}

export function useSearchParams(): AnyObject {
  const { search } = useLocation();
  return useMemo(() => {
    const urlParams = new URLSearchParams(search);
    const params: AnyObject = {};
    for (const [key, value] of urlParams.entries()) {
      params[key] = value;
    }
    return params;
  }, [search]);
}
