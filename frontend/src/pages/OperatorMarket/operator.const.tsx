import { Code } from "lucide-react";
import { OperatorI } from "./operator.model";
import {formatDateTime} from "@/utils/unit.ts";

export const mapOperator = (op: OperatorI) => {
  return {
    ...op,
    icon: <Code className="w-full h-full" />,
    createdAt: formatDateTime(op?.createdAt) || "--",
    updatedAt: formatDateTime(op?.updatedAt) || formatDateTime(op?.createdAt) || "--",
  };
};
