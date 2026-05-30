"use client";
import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Table, TableBody, TableCell,
    TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { Recommendation, approveRecommendation } from "@/lib/api";

interface Props {
    recommendations: Recommendation[];
    onUpdate: () => void;
}

export default function RecommendationsTable({ recommendations, onUpdate }: Props) {
    const [expanded, setExpanded] = useState<number | null>(null);
    const [loading, setLoading] = useState<number | null>(null);

    const handleAction = async (id: number, status: "approved" | "rejected") => {
        setLoading(id);
        try {
            await approveRecommendation(id, status);
            onUpdate();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(null);
        }
    };

    const statusColor = (status: string) => {
        if (status === "approved") return "bg-green-100 text-green-700";
        if (status === "rejected") return "bg-red-100 text-red-700";
        return "bg-orange-100 text-orange-700";
    };

    const priceDiff = (current: number, recommended: number) => {
        const diff = recommended - current;
        const pct = ((diff / current) * 100).toFixed(1);
        return diff >= 0
            ? <span className="text-green-600">+${diff.toFixed(2)} (+{pct}%)</span>
            : <span className="text-red-600">${diff.toFixed(2)} ({pct}%)</span>;
    };

    if (recommendations.length === 0) {
        return (
            <Card>
                <CardContent className="py-10 text-center text-gray-400">
                    No recommendations yet. Click "Run AI Analysis" on a product to generate one.
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border border-gray-100 shadow-sm">
            <CardHeader>
                <CardTitle className="text-base font-semibold text-gray-800">
                    AI Price Recommendations
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <Table>
                    <TableHeader>
                        <TableRow className="bg-gray-50">
                            <TableHead>Product</TableHead>
                            <TableHead>Current</TableHead>
                            <TableHead>Recommended</TableHead>
                            <TableHead>Change</TableHead>
                            <TableHead>Margin</TableHead>
                            <TableHead>Confidence</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {recommendations.map((rec) => (
                            <React.Fragment key={rec.id}>
                                <TableRow
                                    className="cursor-pointer hover:bg-gray-50"
                                    onClick={() => setExpanded(expanded === rec.id ? null : rec.id)}
                                >
                                    <TableCell className="font-medium text-gray-800">
                                        <div className="flex items-center gap-2">
                                            {expanded === rec.id
                                                ? <ChevronUp className="h-4 w-4 text-gray-400" />
                                                : <ChevronDown className="h-4 w-4 text-gray-400" />}
                                            {rec.product_name}
                                        </div>
                                    </TableCell>
                                    <TableCell>${rec.current_price.toFixed(2)}</TableCell>
                                    <TableCell className="font-semibold">
                                        ${rec.recommended_price.toFixed(2)}
                                    </TableCell>
                                    <TableCell>
                                        {priceDiff(rec.current_price, rec.recommended_price)}
                                    </TableCell>
                                    <TableCell>
                                        {rec.expected_margin ? `${rec.expected_margin.toFixed(1)}%` : "—"}
                                    </TableCell>
                                    <TableCell>
                                        {rec.confidence_score ? (
                                            <div className="flex items-center gap-2">
                                                <div className="w-16 bg-gray-200 rounded-full h-1.5">
                                                    <div
                                                        className="bg-blue-500 h-1.5 rounded-full"
                                                        style={{ width: `${rec.confidence_score * 100}%` }}
                                                    />
                                                </div>
                                                <span className="text-xs text-gray-500">
                                                    {(rec.confidence_score * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        ) : "—"}
                                    </TableCell>
                                    <TableCell>
                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor(rec.status)}`}>
                                            {rec.status}
                                        </span>
                                    </TableCell>
                                    <TableCell onClick={(e) => e.stopPropagation()}>
                                        {rec.status === "pending" && (
                                            <div className="flex gap-2">
                                                <Button
                                                    size="sm"
                                                    className="bg-green-600 hover:bg-green-700 text-white h-7 px-2"
                                                    disabled={loading === rec.id}
                                                    onClick={() => handleAction(rec.id, "approved")}
                                                >
                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                    Approve
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="border-red-300 text-red-600 hover:bg-red-50 h-7 px-2"
                                                    disabled={loading === rec.id}
                                                    onClick={() => handleAction(rec.id, "rejected")}
                                                >
                                                    <XCircle className="h-3 w-3 mr-1" />
                                                    Reject
                                                </Button>
                                            </div>
                                        )}
                                    </TableCell>
                                </TableRow>

                                {expanded === rec.id && (
                                    <TableRow className="bg-blue-50">
                                        <TableCell colSpan={8} className="py-3 px-6">
                                            <div className="text-sm">
                                                <p className="font-semibold text-blue-800 mb-1">
                                                    🤖 AI Reasoning
                                                </p>
                                                <p className="text-gray-700">{rec.reasoning}</p>
                                                {rec.avg_competitor_price && (
                                                    <p className="text-gray-500 text-xs mt-2">
                                                        Competitor range: ${rec.min_competitor_price?.toFixed(2)} —
                                                        ${rec.max_competitor_price?.toFixed(2)} |
                                                        Avg: ${rec.avg_competitor_price?.toFixed(2)}
                                                    </p>
                                                )}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )}
                            </React.Fragment>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}