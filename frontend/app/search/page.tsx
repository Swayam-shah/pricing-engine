"use client";
import { useState } from "react";
import { Search, TrendingUp, ShoppingCart, BarChart3, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Listing {
    title: string;
    price: number;
    price_str: string;
    source: string;
    rating?: number;
    reviews?: number;
    link: string;
    thumbnail?: string;
    delivery?: string;
}

interface SearchResult {
    query: string;
    stats: {
        min_price: number;
        max_price: number;
        avg_price: number;
        total_listings: number;
        cheapest: Listing;
        best_deal: Listing;
    };
    insights: {
        seller_recommended_price: number;
        seller_reasoning: string;
        buyer_best_pick: string;
        buyer_reasoning: string;
        market_insight: string;
        price_trend: string;
        competition_level: string;
    };
    listings: Listing[];
}

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SearchResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<"seller" | "buyer">("seller");

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await axios.post(`${API}/api/search`, { query });
            setResult(res.data);
        } catch (e: any) {
            setError(e.response?.data?.detail || "Search failed. Try again.");
        } finally {
            setLoading(false);
        }
    };

    const trendColor = (trend: string) => {
        if (trend === "premium") return "bg-purple-100 text-purple-700";
        if (trend === "competitive") return "bg-orange-100 text-orange-700";
        return "bg-green-100 text-green-700";
    };

    const competitionColor = (level: string) => {
        if (level === "high") return "bg-red-100 text-red-700";
        if (level === "medium") return "bg-orange-100 text-orange-700";
        return "bg-green-100 text-green-700";
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <Button variant="outline" size="sm" className="gap-2">
                                <ArrowLeft className="h-4 w-4" />
                                Dashboard
                            </Button>
                        </Link>
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-600 p-2 rounded-lg">
                                <Search className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-semibold text-gray-900">Market Search</h1>
                                <p className="text-xs text-gray-400">Search any product across all platforms</p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
                {/* Search Bar */}
                <Card className="border border-gray-100 shadow-sm">
                    <CardContent className="pt-6">
                        <div className="flex gap-3">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                                    placeholder='Search any product e.g. "white adidas shoes", "iPhone 15 case"'
                                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <Button
                                onClick={handleSearch}
                                disabled={loading || !query.trim()}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-6"
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                                        Searching...
                                    </span>
                                ) : "Search"}
                            </Button>
                        </div>

                        {/* Quick searches */}
                        <div className="flex gap-2 mt-3 flex-wrap">
                            <span className="text-xs text-gray-400">Try:</span>
                            {["wireless earbuds", "yoga mat", "protein powder", "laptop stand", "running shoes"].map((s) => (
                                <button
                                    key={s}
                                    onClick={() => { setQuery(s); }}
                                    className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-600 transition-colors"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Error */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                        {error}
                    </div>
                )}

                {/* Loading skeleton */}
                {loading && (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-white rounded-lg p-6 animate-pulse">
                                <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
                                <div className="h-3 bg-gray-200 rounded w-2/3" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Results */}
                {result && (
                    <div className="space-y-6">
                        {/* Market Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {[
                                { label: "Lowest Price", value: `₹${result.stats.min_price.toLocaleString()}`, color: "text-green-600" },
                                { label: "Highest Price", value: `₹${result.stats.max_price.toLocaleString()}`, color: "text-red-500" },
                                { label: "Average Price", value: `₹${result.stats.avg_price.toLocaleString()}`, color: "text-blue-600" },
                                { label: "Listings Found", value: result.stats.total_listings, color: "text-purple-600" },
                            ].map((stat) => (
                                <Card key={stat.label} className="border border-gray-100 shadow-sm">
                                    <CardContent className="pt-4 pb-4">
                                        <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
                                        <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Market signals */}
                        <div className="flex gap-3 flex-wrap">
                            <span className="text-sm text-gray-500">Market signals:</span>
                            <span className={`text-xs px-3 py-1 rounded-full font-medium ${trendColor(result.insights.price_trend)}`}>
                                {result.insights.price_trend} pricing
                            </span>
                            <span className={`text-xs px-3 py-1 rounded-full font-medium ${competitionColor(result.insights.competition_level)}`}>
                                {result.insights.competition_level} competition
                            </span>
                            <span className="text-xs px-3 py-1 rounded-full font-medium bg-gray-100 text-gray-600">
                                {result.stats.total_listings} sellers
                            </span>
                        </div>

                        {/* Seller / Buyer tabs */}
                        <div className="flex gap-2">
                            <button
                                onClick={() => setActiveTab("seller")}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === "seller"
                                        ? "bg-blue-600 text-white"
                                        : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
                                    }`}
                            >
                                <TrendingUp className="h-4 w-4" />
                                Seller Intelligence
                            </button>
                            <button
                                onClick={() => setActiveTab("buyer")}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === "buyer"
                                        ? "bg-green-600 text-white"
                                        : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
                                    }`}
                            >
                                <ShoppingCart className="h-4 w-4" />
                                Best Buy Finder
                            </button>
                        </div>

                        {/* Seller View */}
                        {activeTab === "seller" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <Card className="border-2 border-blue-200 shadow-sm">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-base font-semibold text-blue-800 flex items-center gap-2">
                                            <TrendingUp className="h-4 w-4" />
                                            Recommended Seller Price
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-4xl font-bold text-blue-600 mb-3">
                                            ₹{result.insights.seller_recommended_price.toLocaleString()}
                                        </div>
                                        <p className="text-sm text-gray-600 leading-relaxed">
                                            {result.insights.seller_reasoning}
                                        </p>
                                        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                                            <p className="text-xs text-blue-700 font-medium">Market Insight</p>
                                            <p className="text-xs text-blue-600 mt-1">{result.insights.market_insight}</p>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card className="border border-gray-100 shadow-sm">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-base font-semibold text-gray-800 flex items-center gap-2">
                                            <BarChart3 className="h-4 w-4" />
                                            Price Distribution
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {[
                                                { label: "Your recommended price", value: result.insights.seller_recommended_price, color: "bg-blue-500" },
                                                { label: "Market average", value: result.stats.avg_price, color: "bg-gray-400" },
                                                { label: "Lowest competitor", value: result.stats.min_price, color: "bg-green-500" },
                                                { label: "Highest competitor", value: result.stats.max_price, color: "bg-red-400" },
                                            ].map((item) => (
                                                <div key={item.label}>
                                                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                                                        <span>{item.label}</span>
                                                        <span className="font-medium">₹{item.value.toLocaleString()}</span>
                                                    </div>
                                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                                        <div
                                                            className={`${item.color} h-2 rounded-full`}
                                                            style={{
                                                                width: `${Math.min(((item.value - result.stats.min_price) / (result.stats.max_price - result.stats.min_price + 1)) * 100, 100)}%`
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                        {/* Buyer View */}
                        {activeTab === "buyer" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <Card className="border-2 border-green-200 shadow-sm">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-base font-semibold text-green-800 flex items-center gap-2">
                                            <ShoppingCart className="h-4 w-4" />
                                            Best Deal
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex items-start gap-3 mb-3">
                                            {result.stats.best_deal.thumbnail && (
                                                <img
                                                    src={result.stats.best_deal.thumbnail}
                                                    alt={result.stats.best_deal.title}
                                                    className="w-16 h-16 object-contain rounded-lg border border-gray-100"
                                                />
                                            )}
                                            <div>
                                                <p className="text-sm font-medium text-gray-800 line-clamp-2">
                                                    {result.stats.best_deal.title}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">{result.stats.best_deal.source}</p>
                                                <p className="text-2xl font-bold text-green-600 mt-1">
                                                    ₹{result.stats.best_deal.price?.toLocaleString()}
                                                </p>
                                            </div>
                                        </div>
                                        {result.stats.best_deal.rating && (
                                            <div className="flex items-center gap-2 mb-3">
                                                <span className="text-yellow-500">★</span>
                                                <span className="text-sm font-medium">{result.stats.best_deal.rating}</span>
                                                {result.stats.best_deal.reviews && (
                                                    <span className="text-xs text-gray-400">({result.stats.best_deal.reviews.toLocaleString()} reviews)</span>
                                                )}
                                            </div>
                                        )}
                                        <p className="text-sm text-gray-600 leading-relaxed">
                                            {result.insights.buyer_reasoning}
                                        </p>
                                        {result.stats.best_deal.link && (
                                            <a
                                                href={result.stats.best_deal.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="mt-3 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                                            >
                                                View product →
                                            </a>
                                        )}
                                    </CardContent>
                                </Card>

                                <Card className="border border-gray-100 shadow-sm">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-base font-semibold text-gray-800">
                                            Cheapest Option
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex items-start gap-3 mb-3">
                                            {result.stats.cheapest.thumbnail && (
                                                <img
                                                    src={result.stats.cheapest.thumbnail}
                                                    alt={result.stats.cheapest.title}
                                                    className="w-16 h-16 object-contain rounded-lg border border-gray-100"
                                                />
                                            )}
                                            <div>
                                                <p className="text-sm font-medium text-gray-800 line-clamp-2">
                                                    {result.stats.cheapest.title}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">{result.stats.cheapest.source}</p>
                                                <p className="text-2xl font-bold text-red-500 mt-1">
                                                    ₹{result.stats.cheapest.price?.toLocaleString()}
                                                </p>
                                            </div>
                                        </div>
                                        {result.stats.cheapest.rating && (
                                            <div className="flex items-center gap-2">
                                                <span className="text-yellow-500">★</span>
                                                <span className="text-sm font-medium">{result.stats.cheapest.rating}</span>
                                                {result.stats.cheapest.reviews && (
                                                    <span className="text-xs text-gray-400">({result.stats.cheapest.reviews.toLocaleString()} reviews)</span>
                                                )}
                                            </div>
                                        )}
                                        {result.stats.cheapest.link && (
                                            <a
                                                href={result.stats.cheapest.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="mt-3 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                                            >
                                                View product →
                                            </a>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                        {/* All listings table */}
                        <Card className="border border-gray-100 shadow-sm">
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base font-semibold text-gray-800">
                                    All Listings ({result.listings.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-0">
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="bg-gray-50 border-b border-gray-100">
                                                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Product</th>
                                                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Platform</th>
                                                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Price</th>
                                                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Rating</th>
                                                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Reviews</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.listings
                                                .sort((a, b) => (a.price || 0) - (b.price || 0))
                                                .map((listing, i) => (
                                                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                                                        <td className="px-4 py-3">
                                                            <div className="flex items-center gap-2">
                                                                {listing.thumbnail && (
                                                                    <img src={listing.thumbnail} alt="" className="w-8 h-8 object-contain" />
                                                                )}
                                                                <a
                                                                    href={listing.link}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-xs text-gray-700 hover:text-blue-600 line-clamp-1 max-w-xs"
                                                                >
                                                                    {listing.title}
                                                                </a>
                                                            </div>
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <span className="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-600">
                                                                {listing.source}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <span className="text-sm font-semibold text-gray-900">
                                                                ₹{listing.price?.toLocaleString()}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            {listing.rating ? (
                                                                <span className="text-xs text-yellow-600">★ {listing.rating}</span>
                                                            ) : "—"}
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <span className="text-xs text-gray-500">
                                                                {listing.reviews ? listing.reviews.toLocaleString() : "—"}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </main>
        </div>
    );
}