"use client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Package, TrendingUp, CheckCircle, Users } from "lucide-react";
import { DashboardStats } from "@/lib/api";

export default function StatsCards({ stats }: { stats: DashboardStats }) {
    const cards = [
        {
            title: "Total Products",
            value: stats.total_products,
            icon: Package,
            color: "text-blue-600",
            bg: "bg-blue-50",
            suffix: "",
        },
        {
            title: "Pending Reviews",
            value: stats.pending_recommendations,
            icon: TrendingUp,
            color: "text-orange-600",
            bg: "bg-orange-50",
            suffix: " recs",
        },
        {
            title: "Avg Margin",
            value: stats.avg_margin,
            icon: CheckCircle,
            color: "text-green-600",
            bg: "bg-green-50",
            suffix: "%",
        },
        {
            title: "Competitors",
            value: stats.total_competitors,
            icon: Users,
            color: "text-purple-600",
            bg: "bg-purple-50",
            suffix: "",
        },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {cards.map((card) => (
                <Card key={card.title} className="border border-gray-100 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-gray-500">
                            {card.title}
                        </CardTitle>
                        <div className={`p-2 rounded-lg ${card.bg}`}>
                            <card.icon className={`h-4 w-4 ${card.color}`} />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-gray-900">
                            {typeof card.value === "number" && card.suffix === "%"
                                ? card.value.toFixed(1)
                                : card.value}
                            <span className="text-sm font-normal text-gray-500">
                                {card.suffix}
                            </span>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}