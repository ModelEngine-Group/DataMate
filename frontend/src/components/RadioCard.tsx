import React from "react";
import { Card } from "antd";

interface RadioCardOption {
  value: string;
  label: string;
  description?: string;
  icon?: SVGAElement | React.FC<React.SVGProps<SVGElement>>;
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
      className={`grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 ${
        className || ""
      }`}
      style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}
    >
      {options.map((option) => (
        <div
          key={option.value}
          className="border border-gray-200 rounded-lg hover:shadow-lg p-4 text-center"
          style={{
            borderColor: value === option.value ? "#1677ff" : undefined,
            background: value === option.value ? "#e6f7ff" : undefined,
            cursor: "pointer",
          }}
          onClick={() => onChange(option.value)}
        >
          <option.icon
            className={`w-8 h-8 mx-auto mb-2 ${
              value === option.value ? "text-blue-500" : "text-gray-400"
            }`}
          />
          <h3
            className={`font-medium text-sm mb-1 ${
              value === option.value ? "text-blue-500" : "text-gray-900"
            }`}
          >
            {option.label}
          </h3>
          {option.description && (
            <div
              className={`text-xs ${
                value === option.value ? "text-blue-500" : "text-gray-500"
              }`}
            >
              {option.description}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default RadioCard;
