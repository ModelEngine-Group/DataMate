

import { Button } from "antd";
import OperatorUpload from "@/app/(layout)/operator-market/components/operator-upload";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function OperatorUpdatePage() {
    const router = useRouter();
    return (
        <div className="h-screen bg-gray-50">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button onClick={() => router.push("/operator-market")} className="flex items-center gap-2">
                    <ArrowLeft className="w-4 h-4" />
                </Button>
                <h1 className="text-2xl font-bold text-gray-900">更新算子</h1>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <OperatorUpload />
            </div>
        </div>
    );
}