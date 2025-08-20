import React from "react";
import { Card } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";

interface RadioCardOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  color?: string;
}

interface RadioCardProps {
  options: RadioCardOption[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

const RadioCard: React.FC<RadioCardProps> = ({
  options,
  value,
  onChange,
  className,
}) => {
  return (
    <div
      className={`grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 ${className || ""}`}
      style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}
    >
      {options.map((option) => (
        <Card
          key={option.value}
          hoverable
          style={{
            borderColor: value === option.value ? "#1677ff" : undefined,
            background: value === option.value ? "#e6f7ff" : undefined,
            cursor: "pointer",
          }}
          onClick={() => onChange(option.value)}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 8,
            }}
          >
            {option.icon && <span style={{ fontSize: 24 }}>{option.icon}</span>}
            <span style={{ fontWeight: 500 }}>{option.label}</span>
          </div>
          {option.description && (
            <div style={{ color: "#888", fontSize: 13 }}>{option.description}</div>
          )}
        </Card>
      ))}
    </div>
  );
};

export default RadioCard;
