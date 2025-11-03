import { Button, Card, Input, InputNumber, Popconfirm, Select, Switch, Tooltip } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { useState, useImperativeHandle, forwardRef } from "react";

type LabelType = "string" | "number" | "enum";

type LabelItem = {
    id: string;
    name: string;
    type: LabelType;
    required?: boolean;
    // for enum: values; for number: min/max
    values?: string[];
    min?: number | null;
    max?: number | null;
    step?: number | null;
};

type LabelingConfigEditorProps = {
    initial?: any;
    onGenerate: (config: any) => void;
    hideFooter?: boolean;
};

export default forwardRef<any, LabelingConfigEditorProps>(function LabelingConfigEditor(
    { initial, onGenerate, hideFooter }: LabelingConfigEditorProps,
    ref: any
) {
    const [labels, setLabels] = useState<LabelItem[]>(() => {
        if (initial && initial.labels && Array.isArray(initial.labels)) {
            return initial.labels.map((l: any, idx: number) => ({
                id: `${Date.now()}-${idx}`,
                name: l.name || "",
                type: l.type || "string",
                required: !!l.required,
                values: l.values || (l.type === "enum" ? [] : undefined),
                min: l.min ?? null,
                max: l.max ?? null,
            }));
        }
        return [];
    });

    const addLabel = () => {
        setLabels((s) => [
            ...s,
            { id: `${Date.now()}-${Math.random()}`, name: "", type: "string", required: false, step: null },
        ]);
    };

    const updateLabel = (id: string, patch: Partial<LabelItem>) => {
        setLabels((s) => s.map((l) => (l.id === id ? { ...l, ...patch } : l)));
    };

    const removeLabel = (id: string) => {
        setLabels((s) => s.filter((l) => l.id !== id));
    };

    const generate = () => {
        // basic validation: label name non-empty
        for (const l of labels) {
            if (!l.name || l.name.trim() === "") {
                // focus not available here, just abort
                // Could show a more friendly UI; keep simple for now
                // eslint-disable-next-line no-alert
                alert("请为所有标签填写名称");
                return;
            }
            if (l.type === "enum") {
                if (!l.values || l.values.length === 0) {
                    alert(`枚举标签 ${l.name} 需要至少一个取值`);
                    return;
                }
            }
            if (l.type === "number") {
                // validate min/max
                if (l.min != null && l.max != null && l.min > l.max) {
                    alert(`数值标签 ${l.name} 的最小值不能大于最大值`);
                    return;
                }
                // validate step
                if (l.step != null && (!(typeof l.step === "number") || l.step <= 0)) {
                    alert(`数值标签 ${l.name} 的步长必须为大于 0 的数值`);
                    return;
                }
            }
        }

        const config = {
            labels: labels.map((l) => {
                const item: any = { name: l.name, type: l.type, required: !!l.required };
                if (l.type === "enum") item.values = l.values || [];
                if (l.type === "number") {
                    if (l.min != null) item.min = l.min;
                    if (l.max != null) item.max = l.max;
                }
                return item;
            }),
        };

        onGenerate(config);
    };

    useImperativeHandle(ref, () => ({
        addLabel,
        generate,
    }));

    return (
        <div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {labels.map((label) => (
                    <Card size="small" key={label.id} styles={{ body: { padding: 10 } }}>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                            <Input
                                placeholder="标签名称"
                                value={label.name}
                                onChange={(e) => updateLabel(label.id, { name: e.target.value })}
                                style={{ flex: "1 1 160px", minWidth: 120 }}
                            />
                            <Select
                                value={label.type}
                                onChange={(v) => updateLabel(label.id, { type: v as LabelType })}
                                options={[{ label: "文本", value: "string" }, { label: "数值", value: "number" }, { label: "枚举", value: "enum" }]}
                                style={{ width: 120, flex: "0 0 120px" }}
                            />

                            {label.type === "enum" && (
                                <Input.TextArea
                                    placeholder="每行一个枚举值，按回车换行"
                                    value={(label.values || []).join("\n")}
                                    onChange={(e) => updateLabel(label.id, { values: e.target.value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean) })}
                                    onKeyDown={(e) => {
                                        // Prevent parent handlers (like Form submit or modal shortcuts) from intercepting Enter
                                        e.stopPropagation();
                                    }}
                                    rows={3}
                                    style={{ flex: "1 1 220px", minWidth: 160, width: "100%", resize: "vertical" }}
                                />
                            )}

                            {label.type === "number" && (
                                <div style={{ display: "flex", gap: 8, alignItems: "center", flex: "0 0 auto" }}>
                                    <Tooltip title="最小值">
                                        <InputNumber value={label.min ?? null} onChange={(v) => updateLabel(label.id, { min: v ?? null })} placeholder="min" />
                                    </Tooltip>
                                    <Tooltip title="最大值">
                                        <InputNumber value={label.max ?? null} onChange={(v) => updateLabel(label.id, { max: v ?? null })} placeholder="max" />
                                    </Tooltip>
                                    <Tooltip title="步长 (step)">
                                        <InputNumber value={label.step ?? null} onChange={(v) => updateLabel(label.id, { step: v ?? null })} placeholder="step" min={0} />
                                    </Tooltip>
                                </div>
                            )}

                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: "auto" }}>
                                <span style={{ fontSize: 12, color: "rgba(0,0,0,0.65)" }}>必填</span>
                                <Switch checked={!!label.required} onChange={(v) => updateLabel(label.id, { required: v })} />
                                <Popconfirm title="确认删除该标签？" onConfirm={() => removeLabel(label.id)}>
                                    <Button type="text" icon={<DeleteOutlined />} />
                                </Popconfirm>
                            </div>
                        </div>
                        <div style={{ marginTop: 8, color: "rgba(0,0,0,0.45)", fontSize: 12 }}>
                            {label.type === "string" && <span>类型：文本</span>}
                            {label.type === "number" && <span>类型：数值，支持 min / max / step</span>}
                            {label.type === "enum" && <span>类型：枚举，每行一个取值（示例：一行写一个值）</span>}
                        </div>
                    </Card>
                ))}

                {!hideFooter && (
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button icon={<PlusOutlined />} onClick={addLabel}>
                            添加标签
                        </Button>
                        <Button type="primary" onClick={generate}>
                            生成 JSON 配置
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}

);
