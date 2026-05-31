"use client";
import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, Zap, TrendingUp, Search } from "lucide-react";
import Link from "next/link";
import StatsCards from "@/components/StatsCards";
import PriceChart from "@/components/PriceChart";
import RecommendationsTable from "@/components/RecommendationsTable";
import {
  getProducts, getDashboardStats, getRecommendations,
  getPriceHistory, analyzeProduct,
  Product, Recommendation, DashboardStats, PriceHistory,
} from "@/lib/api";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistory | null>(null);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchAll = useCallback(async () => {
    try {
      const [s, p, r] = await Promise.all([
        getDashboardStats(),
        getProducts(),
        getRecommendations(),
      ]);
      setStats(s);
      setProducts(p);
      setRecommendations(r);
      setLastUpdated(new Date());

      if (p.length > 0 && !selectedProduct) {
        setSelectedProduct(p[0]);
      }
    } catch (e) {
      console.error("Failed to fetch data:", e);
    } finally {
      setLoading(false);
    }
  }, [selectedProduct]);

  const fetchPriceHistory = useCallback(async (productId: number) => {
    try {
      const history = await getPriceHistory(productId);
      setPriceHistory(history);
    } catch (e) {
      console.error("Failed to fetch price history:", e);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      fetchPriceHistory(selectedProduct.id);
    }
  }, [selectedProduct]);

  useEffect(() => {
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const handleAnalyze = async (productId: number) => {
    setAnalyzing(productId);
    try {
      await analyzeProduct(productId);
      await fetchAll();
    } catch (e) {
      console.error("Analysis failed:", e);
    } finally {
      setAnalyzing(null);
    }
  };

  const margin = (product: Product) =>
    (((product.our_price - product.cost_price) / product.our_price) * 100).toFixed(1);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Loading Pricing Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">PriceIQ</h1>
              <p className="text-xs text-gray-400">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/search">
              <Button
                className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                size="sm"
              >
                <Search className="h-4 w-4" />
                Market Search
              </Button>
            </Link>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchAll}
              className="gap-2 text-gray-600"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Stats Cards */}
        {stats && <StatsCards stats={stats} />}

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Products list */}
          <Card className="border border-gray-100 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-gray-800">
                Products
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {products.map((product) => (
                <div
                  key={product.id}
                  onClick={() => setSelectedProduct(product)}
                  className={`px-4 py-3 border-b last:border-0 cursor-pointer transition-colors ${selectedProduct?.id === product.id
                      ? "bg-blue-50 border-l-2 border-l-blue-600"
                      : "hover:bg-gray-50"
                    }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-800 truncate pr-2">
                      {product.name}
                    </p>
                    <span className="text-sm font-bold text-gray-900 shrink-0">
                      ${product.our_price.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">{product.category}</span>
                    <span className="text-xs text-green-600 font-medium">
                      {margin(product)}% margin
                    </span>
                  </div>
                  <Button
                    size="sm"
                    className="mt-2 w-full h-7 text-xs bg-blue-600 hover:bg-blue-700 text-white gap-1"
                    disabled={analyzing === product.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAnalyze(product.id);
                    }}
                  >
                    {analyzing === product.id ? (
                      <>
                        <RefreshCw className="h-3 w-3 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-3 w-3" />
                        Run AI Analysis
                      </>
                    )}
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Price chart */}
          <Card className="lg:col-span-2 border border-gray-100 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-gray-800">
                Price History — {selectedProduct?.name ?? "Select a product"}
              </CardTitle>
              <div className="flex gap-4 text-xs text-gray-500 mt-1">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-blue-500 inline-block" /> Our Price
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-red-400 inline-block" /> Competitor Avg
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-green-500 inline-block" /> AI Recommended
                </span>
              </div>
            </CardHeader>
            <CardContent>
              {priceHistory ? (
                <PriceChart data={priceHistory} />
              ) : (
                <div className="h-72 flex items-center justify-center text-gray-400 text-sm">
                  Select a product to view price history
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <div>
          <Tabs defaultValue="pending">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800">
                AI Recommendations
              </h2>
              <TabsList className="bg-gray-100">
                <TabsTrigger value="pending" className="text-xs">
                  Pending ({recommendations.filter(r => r.status === "pending").length})
                </TabsTrigger>
                <TabsTrigger value="all" className="text-xs">
                  All ({recommendations.length})
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="pending">
              <RecommendationsTable
                recommendations={recommendations.filter(r => r.status === "pending")}
                onUpdate={fetchAll}
              />
            </TabsContent>
            <TabsContent value="all">
              <RecommendationsTable
                recommendations={recommendations}
                onUpdate={fetchAll}
              />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}