import React from "react";
import { Card } from "antd";

interface RadioCardOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ElementType;
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
      className={`grid xs:grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 ${
        className || ""
      }`}
    >
      {options.map((option) => (
        <Card
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`cursor-pointer transition-all ${
            value === option.value ? "border border-blue-500 shadow" : ""
          }`}
        >
          <div className="text-center">
            {option.icon && (
              <option.icon
                className={`w-8 h-8 mx-auto mb-2 ${
                  value === option.value
                    ? option.color?.split(" ")[2] || "text-blue-500"
                    : "text-gray-400"
                }`}
              />
            )}
            <h3
              className={`font-medium text-sm mb-1 ${
                value === option.value
                  ? option.color?.split(" ")[2] || "text-blue-500"
                  : "text-gray-900"
              }`}
            >
              {option.label}
            </h3>
            {option.description && (
              <p
                className={`text-xs ${
                  value === option.value
                    ? option.color?.split(" ")[2] || "text-blue-500"
                    : "text-gray-500"
                }`}
              >
                {option.description}
              </p>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};

export default RadioCard;
