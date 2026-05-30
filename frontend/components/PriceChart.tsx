"use client";
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { PriceHistory } from "@/lib/api";

export default function PriceChart({ data }: { data: PriceHistory }) {
    const chartData = data.history.slice(-14).map((p) => ({
        date: p.date.slice(5),
        "Our Price": p.our_price,
        "Competitor Avg": p.competitor_avg ?? undefined,
        "AI Recommended": p.recommended_price ?? undefined,
    }));

    return (
        <div style={{ width: "100%", height: "300px", minHeight: "300px", display: "block" }}>
            <ResponsiveContainer width="100%" height="100%" minHeight={300}>
                <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#6b7280" }} />
                    <YAxis
                        tick={{ fontSize: 12, fill: "#6b7280" }}
                        tickFormatter={(v) => `$${v}`}
                    />
                    <Tooltip formatter={(value) => [`$${Number(value).toFixed(2)}`, ""]} />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="Our Price"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="Competitor Avg"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="5 5"
                    />
                    <Line
                        type="monotone"
                        dataKey="AI Recommended"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="3 3"
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}