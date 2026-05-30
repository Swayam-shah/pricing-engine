"""
LangGraph Pricing Agent
-----------------------
Wires the 4 nodes into a directed graph:
START → fetch_data → run_analysis → generate_price → save_result → END

The graph takes a product_id as input and returns a full
PricingState with the recommendation saved to the database.
"""
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.state import PricingState
from agents.nodes import fetch_data, run_analysis, generate_price, save_result


def build_pricing_graph(db: Session):
    """
    Builds and compiles the LangGraph pricing agent.
    We pass the db session in so every node can access the database.
    """

    # wrap each node so it receives the db session automatically
    def node_fetch(state: PricingState) -> PricingState:
        return fetch_data(state, db)

    def node_analysis(state: PricingState) -> PricingState:
        return run_analysis(state, db)

    def node_generate(state: PricingState) -> PricingState:
        return generate_price(state, db)

    def node_save(state: PricingState) -> PricingState:
        return save_result(state, db)

    def should_continue(state: PricingState) -> str:
        """
        After each node, check if there's an error.
        If yes → stop early. If no → continue to next node.
        """
        if state.get("error"):
            print(f"\n🛑 Stopping graph due to error: {state['error']}")
            return "end"
        return "continue"

    # ── Build the graph ───────────────────────────────────────────────────
    graph = StateGraph(PricingState)

    # add nodes
    graph.add_node("fetch_data", node_fetch)
    graph.add_node("run_analysis", node_analysis)
    graph.add_node("generate_price", node_generate)
    graph.add_node("save_result", node_save)

    # set entry point
    graph.set_entry_point("fetch_data")

    # add conditional edges — stop if error, continue if ok
    graph.add_conditional_edges(
        "fetch_data",
        should_continue,
        {"continue": "run_analysis", "end": END}
    )
    graph.add_conditional_edges(
        "run_analysis",
        should_continue,
        {"continue": "generate_price", "end": END}
    )
    graph.add_conditional_edges(
        "generate_price",
        should_continue,
        {"continue": "save_result", "end": END}
    )
    graph.add_edge("save_result", END)

    return graph.compile()


def run_pricing_agent(product_id: int, db: Session) -> PricingState:
    """
    Main entry point — call this to run the full pricing agent for a product.
    Returns the final state with recommendation details.
    """
    print(f"\n{'='*50}")
    print(f"🚀 Starting Pricing Agent for product_id={product_id}")
    print(f"{'='*50}")

    app = build_pricing_graph(db)

    initial_state: PricingState = {
        "product_id": product_id,
        "product_name": None,
        "our_price": None,
        "cost_price": None,
        "competitor_prices": None,
        "avg_units_sold": None,
        "avg_revenue": None,
        "min_competitor_price": None,
        "max_competitor_price": None,
        "avg_competitor_price": None,
        "current_margin_pct": None,
        "price_vs_competitor": None,
        "analysis_summary": None,
        "recommended_price": None,
        "expected_margin": None,
        "confidence_score": None,
        "reasoning": None,
        "recommendation_id": None,
        "error": None,
    }

    final_state = app.invoke(initial_state)

    print(f"\n{'='*50}")
    if final_state.get("error"):
        print(f"❌ Agent failed: {final_state['error']}")
    else:
        print(f"✅ Agent complete!")
        print(f"   Product: {final_state['product_name']}")
        print(f"   Current price: ${final_state['our_price']}")
        print(f"   Recommended:   ${final_state['recommended_price']}")
        print(f"   Margin:        {final_state['expected_margin']}%")
        print(f"   Reasoning:     {final_state['reasoning']}")
        print(f"   Saved as recommendation ID: {final_state['recommendation_id']}")
    print(f"{'='*50}\n")

    return final_state