import sys
from pycommerce.plugins.shipping.calculator import ShippingRateCalculator, ShippingZone

def test_premium_shipping():
    """Test the premium shipping option in the ShippingRateCalculator."""
    
    # Create a calculator instance
    calculator = ShippingRateCalculator()
    
    # Sample items with weights and dimensions
    items = [
        {
            "name": "T-shirt",
            "weight": 0.2,  # 200g
            "quantity": 2,
            "dimensions": {
                "width": 25,
                "height": 5,
                "length": 35
            }
        },
        {
            "name": "Jeans",
            "weight": 0.8,  # 800g
            "quantity": 1,
            "dimensions": {
                "width": 40,
                "height": 5,
                "length": 50
            }
        }
    ]
    
    # Calculate shipping rates
    origin_country = "US"
    destination_country = "US"
    
    rates = calculator.calculate_rates(items, origin_country, destination_country)
    
    # Print the results
    print("\nShipping Rate Calculator Test")
    print("==========================")
    print(f"Origin country: {origin_country}")
    print(f"Destination country: {destination_country}")
    
    print("\nItems:")
    for item in items:
        print(f"  - {item['quantity']}x {item['name']}, {item['weight']}kg each")
    
    print("\nShipping Options:")
    for rate in rates:
        print(f"\n{rate['name']} (ID: {rate['id']})")
        print(f"  Price: ${rate['price']:.2f}")
        print(f"  Delivery: {rate['description']}")
        print(f"  Estimated Days: {rate['estimated_days']}")
        print(f"  Zone: {rate['zone']}")
        print(f"  Billable Weight: {rate['billable_weight']}kg")
        print(f"  Free Shipping: {'Yes' if rate['free_shipping'] else 'No'}")
    
    # Verify that we got all three shipping options
    shipping_methods = [rate['id'] for rate in rates]
    expected_methods = ['standard', 'express', 'premium']
    
    for method in expected_methods:
        if method not in shipping_methods:
            print(f"\nERROR: {method} shipping method not found!")
            sys.exit(1)
    
    print("\nSuccess! All shipping methods were found.")
    
    # Test with international shipping
    print("\n\nInternational Shipping Test (US to UK)")
    print("===================================")
    
    international_rates = calculator.calculate_rates(items, "US", "GB")
    
    print("\nShipping Options:")
    for rate in international_rates:
        print(f"\n{rate['name']} (ID: {rate['id']})")
        print(f"  Price: ${rate['price']:.2f}")
        print(f"  Delivery: {rate['description']}")
        print(f"  Estimated Days: {rate['estimated_days']}")
        print(f"  Zone: {rate['zone']}")
    
    print("\nDone!")

if __name__ == "__main__":
    test_premium_shipping()