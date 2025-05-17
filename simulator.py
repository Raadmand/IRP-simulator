import statistics
from collections import defaultdict
import pandas as pd

def run_irp_simulation_with_intervention(
    initial_prices,
    volumes,
    irp_policies,
    intervention=None,
    years=10
):
    def compute_irp_price(prices_by_country, basket, rule, year):
        basket_prices = [
            prices_by_country[c][year] for c in basket if year in prices_by_country[c]
        ]
        if not basket_prices:
            return None
        if rule == "min":
            return min(basket_prices)
        elif rule == "average":
            return sum(basket_prices) / len(basket_prices)
        elif rule == "median":
            return statistics.median(basket_prices)
        else:
            raise ValueError(f"Unknown rule: {rule}")

    price_time_series = defaultdict(lambda: defaultdict(dict))
    irp_events = defaultdict(lambda: defaultdict(dict))
    YEARS = range(0, years + 1)

    for drug, countries in initial_prices.items():
        for country, price in countries.items():
            price_time_series[drug][country][0] = price

    for year in YEARS[1:]:
        for drug in initial_prices:
            for country in initial_prices[drug]:
                prev_price = price_time_series[drug][country].get(year - 1)
                if prev_price is not None:
                    price_time_series[drug][country][year] = prev_price

            for country, policy in irp_policies.items():
                freq = policy.get("frequency", 1)
                delay = policy.get("enforcement_delay", 0)
                collect_year = year - delay
                if collect_year >= 0 and collect_year % freq == 0:
                    basket = policy.get("basket", [])
                    rule = policy.get("rule", "average")
                    ref_prices = price_time_series[drug]
                    irp_price = compute_irp_price(ref_prices, basket, rule, collect_year)
                    enforce_year = collect_year + delay
                    if enforce_year <= years:
                        irp_events[drug][country][enforce_year] = irp_price

        for drug in irp_events:
            for country in irp_events[drug]:
                if year in irp_events[drug][country]:
                    new_price = irp_events[drug][country][year]
                    price_time_series[drug][country][year] = round(new_price, 2)

        if intervention:
            if (
                intervention["year"] == year and
                intervention["drug"] in price_time_series and
                intervention["country"] in price_time_series[intervention["drug"]]
            ):
                original_price = price_time_series[intervention["drug"]][intervention["country"]][year]
                reduction = intervention["reduction_pct"]
                adjusted_price = round(original_price * (1 - reduction), 2)
                price_time_series[intervention["drug"]][intervention["country"]][year] = adjusted_price

    output_rows = []
    for drug in price_time_series:
        for country in price_time_series[drug]:
            for year in YEARS:
                price = price_time_series[drug][country].get(year)
                volume = volumes.get(drug, {}).get(country, {}).get(year, 0)
                revenue = round(price * volume, 2) if price is not None else None
                output_rows.append({
                    "Drug": drug,
                    "Country": country,
                    "Year": year,
                    "Price": price,
                    "Volume": volume,
                    "Revenue": revenue
                })

    return pd.DataFrame(output_rows)
