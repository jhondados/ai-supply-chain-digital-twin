"""Supply chain digital twin simulator."""
from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta

class SupplyChainTwin:
    def __init__(self, products: List[Dict], suppliers: List[Dict], warehouses: List[Dict]):
        self.products = {p["sku"]: p for p in products}
        self.suppliers = {s["id"]: s for s in suppliers}
        self.warehouses = {w["id"]: w for w in warehouses}
        self.inventory = {p["sku"]: p.get("initial_stock", 0) for p in products}
        self.pending_orders = []
        self.simulation_log = []

    def simulate_day(self, demand: Dict[str, int], date: datetime = None) -> Dict:
        """Run one day of supply chain simulation."""
        date = date or datetime.now()
        events = []
        # Fulfill demand
        stockouts = []
        for sku, qty in demand.items():
            if self.inventory.get(sku, 0) >= qty:
                self.inventory[sku] -= qty
                events.append({"type": "demand_fulfilled", "sku": sku, "qty": qty})
            else:
                available = self.inventory.get(sku, 0)
                shortage = qty - available
                self.inventory[sku] = 0
                stockouts.append({"sku": sku, "shortage": shortage})
                events.append({"type": "stockout", "sku": sku, "shortage": shortage})
        # Receive orders
        arrived = [o for o in self.pending_orders if o["arrival_date"] <= date]
        for order in arrived:
            self.inventory[order["sku"]] = self.inventory.get(order["sku"], 0) + order["qty"]
            events.append({"type": "order_received", "sku": order["sku"], "qty": order["qty"]})
        self.pending_orders = [o for o in self.pending_orders if o["arrival_date"] > date]
        state = {"date": str(date.date()), "inventory": dict(self.inventory),
                 "stockouts": stockouts, "events": events,
                 "service_level": 1 - len(stockouts) / max(len(demand), 1)}
        self.simulation_log.append(state)
        return state

    def recommend_reorders(self, forecast: Dict[str, List[float]], lead_time_days: int = 7) -> List[Dict]:
        """Recommend reorder quantities based on demand forecast."""
        reorders = []
        for sku, forecast_vals in forecast.items():
            horizon_demand = sum(forecast_vals[:lead_time_days + 7])
            safety_stock = np.std(forecast_vals) * 1.64  # 95% service level
            reorder_point = horizon_demand + safety_stock
            current = self.inventory.get(sku, 0)
            if current < reorder_point:
                qty = int(reorder_point * 1.5 - current)
                reorders.append({"sku": sku, "qty": qty, "urgency": "high" if current < horizon_demand * 0.5 else "normal"})
        return reorders
