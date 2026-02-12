import { useState, useEffect } from "react";
import { message } from "antd";
import { useTranslation } from "react-i18next";
import { getTagConfigUsingGet } from "../pages/DataAnnotation/annotation.api";
import type { LabelStudioTagConfig } from "../pages/DataAnnotation/annotation.tagconfig";
import { parseTagConfig, type TagOption } from "../pages/DataAnnotation/annotation.tagconfig";

interface UseTagConfigReturn {
    config: LabelStudioTagConfig | null;
    objectOptions: TagOption[];
    controlOptions: TagOption[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage Label Studio tag configuration
 * @param includeLabelingOnly - If true, only include controls with category="labeling" (default: true)
 */
export function useTagConfig(includeLabelingOnly: boolean = true): UseTagConfigReturn {
    const { t } = useTranslation();
    const [config, setConfig] = useState<LabelStudioTagConfig | null>(null);
    const [objectOptions, setObjectOptions] = useState<TagOption[]>([]);
    const [controlOptions, setControlOptions] = useState<TagOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchConfig = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getTagConfigUsingGet();
            if (response.data) {
                const tagConfig: LabelStudioTagConfig = response.data;
                setConfig(tagConfig);

                const { objectOptions: objects, controlOptions: controls } =
                    parseTagConfig(tagConfig, includeLabelingOnly);
                setObjectOptions(objects);
                setControlOptions(controls);
            } else {
                const errorMsg = response.message || t('hooks.tagConfig.fetchFailed');
                setError(errorMsg);
                message.error(errorMsg);
            }
        } catch (err: any) {
            const errorMsg = err.message || t('hooks.tagConfig.loadError');
            setError(errorMsg);
            console.error("Failed to fetch tag config:", err);
            message.error(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    return {
        config,
        objectOptions,
        controlOptions,
        loading,
        error,
        refetch: fetchConfig,
    };
}
