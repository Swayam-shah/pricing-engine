import axios from "axios";

const API = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

// ── Types ─────────────────────────────────────────────────────────────────────
export interface Product {
    id: number;
    name: string;
    sku: string;
    our_price: number;
    cost_price: number;
    category: string;
}

export interface Recommendation {
    id: number;
    product_id: number;
    product_name: string;
    current_price: number;
    recommended_price: number;
    min_competitor_price: number | null;
    max_competitor_price: number | null;
    avg_competitor_price: number | null;
    expected_margin: number | null;
    confidence_score: number | null;
    reasoning: string | null;
    status: string;
    approved_at: string | null;
    created_at: string;
}

export interface DashboardStats {
    total_products: number;
    pending_recommendations: number;
    approved_today: number;
    avg_margin: number;
    total_competitors: number;
    last_scrape: string | null;
}

export interface PriceHistoryPoint {
    date: string;
    our_price: number;
    competitor_avg: number | null;
    recommended_price: number | null;
}

export interface PriceHistory {
    product_id: number;
    product_name: string;
    history: PriceHistoryPoint[];
}

// ── API calls ─────────────────────────────────────────────────────────────────
export const getProducts = async (): Promise<Product[]> => {
    const res = await API.get("/api/products");
    return res.data;
};

export const getDashboardStats = async (): Promise<DashboardStats> => {
    const res = await API.get("/api/dashboard/stats");
    return res.data;
};

export const getRecommendations = async (status?: string): Promise<Recommendation[]> => {
    const res = await API.get("/api/recommendations", {
        params: status ? { status } : {},
    });
    return res.data;
};

export const getPriceHistory = async (productId: number): Promise<PriceHistory> => {
    const res = await API.get(`/api/products/${productId}/price-history`);
    return res.data;
};

export const analyzeProduct = async (productId: number): Promise<Recommendation> => {
    const res = await API.post(`/api/analyze/${productId}`);
    return res.data;
};

export const approveRecommendation = async (
    recId: number,
    status: "approved" | "rejected"
): Promise<any> => {
    const res = await API.patch(`/api/recommendations/${recId}/approve`, { status });
    return res.data;
};