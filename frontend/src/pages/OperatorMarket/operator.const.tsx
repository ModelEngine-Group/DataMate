import { Code } from "lucide-react";
import { OperatorI } from "./operator.model";

export const mapOperator = (op: OperatorI) => {
  return {
    ...op,
    icon: <Code className="w-full h-full" />,
  };
};
