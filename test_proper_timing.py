#!/usr/bin/env python3
"""
Test proper timing for reservation modification and cancellation
"""
import requests
from datetime import datetime, date, timedelta
import json

def test_proper_timing():
    base_url = "https://boutique-reserve-hub.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as guest
    login_data = {"email": "huesped@test.com", "password": "Huesped123!"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("🔍 TESTING WITH PROPER TIMING (>48 hours in future)\n")
    
    # Create dates >48 hours in future
    checkin_date = date.today() + timedelta(days=5)  # 5 days from now
    checkout_date = date.today() + timedelta(days=7)  # 7 days from now
    
    # Get available rooms
    params = {
        'fecha_checkin': checkin_date.isoformat(),
        'fecha_checkout': checkout_date.isoformat()
    }
    
    response = requests.get(f"{api_url}/habitaciones/disponibilidad", headers=headers, params=params)
    rooms = response.json()['habitaciones_disponibles']
    
    if not rooms:
        print("❌ No available rooms found")
        return False, False
    
    room = rooms[0]
    print(f"✅ Selected room: {room['numero']} for dates {checkin_date} to {checkout_date}")
    
    # Create reservation
    reservation_data = {
        "habitacion_id": room['id'],
        "fecha_checkin": checkin_date.isoformat(),
        "fecha_checkout": checkout_date.isoformat(),
        "num_huespedes": 2,
        "huesped": {
            "nombre_completo": "Future Test User",
            "documento": "FUTURE123",
            "email": "future@test.com",
            "telefono": "3007777777",
            "ciudad": "Bogotá",
            "pais": "Colombia"
        },
        "metodo_pago": "tarjeta_credito"
    }
    
    response = requests.post(f"{api_url}/reservas", headers=headers, json=reservation_data)
    
    if response.status_code != 201:
        print(f"❌ Failed to create reservation: {response.status_code}")
        return False, False
    
    reservation = response.json()
    print(f"✅ Created reservation: {reservation['codigo']} (${reservation['precio_total']:,.0f})")
    
    # Calculate timing
    now = datetime.now()
    checkin_dt = datetime.combine(checkin_date, datetime.min.time())
    hours_until = (checkin_dt - now).total_seconds() / 3600
    print(f"   Hours until check-in: {hours_until:.1f} hours ({hours_until/24:.1f} days)")
    
    # Test 1: Modify reservation (should work >24h)
    print(f"\n🔧 TESTING RESERVATION MODIFICATION")
    
    new_checkout = checkout_date + timedelta(days=1)  # Extend by one day
    modify_data = {
        "fecha_checkout": new_checkout.isoformat(),
        "notas": "Extended stay - proper timing test"
    }
    
    response = requests.put(f"{api_url}/reservas/{reservation['id']}", headers=headers, json=modify_data)
    
    modification_success = response.status_code == 200
    print(f"   Modification Status: {response.status_code}")
    
    if modification_success:
        updated_res = response.json()
        print(f"   ✅ Successfully modified checkout to: {updated_res['fecha_checkout']}")
        print(f"   ✅ New price: ${updated_res['precio_total']:,.0f}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Test 2: Cancel reservation (should get 100% refund >48h)
    print(f"\n❌ TESTING RESERVATION CANCELLATION")
    
    cancel_data = {"motivo": "Proper timing test - should get 100% refund"}
    
    response = requests.post(f"{api_url}/reservas/{reservation['id']}/cancelar", headers=headers, json=cancel_data)
    
    cancellation_success = False
    if response.status_code == 200:
        cancel_result = response.json()
        refund_percentage = cancel_result.get('porcentaje_reembolso', 0)
        
        print(f"   ✅ Cancellation Status: {response.status_code}")
        print(f"   Original Amount: ${cancel_result.get('monto_original', 0):,.0f}")
        print(f"   Refund Amount: ${cancel_result.get('monto_reembolso', 0):,.0f}")
        print(f"   Refund Percentage: {refund_percentage}%")
        print(f"   Policy Applied: {cancel_result.get('politica_aplicada', 'N/A')}")
        
        # Should be 100% refund for >48h cancellation
        cancellation_success = refund_percentage == 100.0
        
        if cancellation_success:
            print(f"   ✅ Correct 100% refund policy applied!")
        else:
            print(f"   ❌ Expected 100% refund, got {refund_percentage}%")
    else:
        print(f"   ❌ Cancellation failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    return modification_success, cancellation_success

if __name__ == "__main__":
    mod_success, cancel_success = test_proper_timing()
    
    print(f"\n📝 FINAL RESULTS:")
    print(f"   RF-03 Modification: {'✅ PASS' if mod_success else '❌ FAIL'}")
    print(f"   RF-04 Cancellation: {'✅ PASS' if cancel_success else '❌ FAIL'}")
    
    if mod_success and cancel_success:
        print(f"\n🎉 Both business rules are working correctly!")
        print(f"   The original test failures were due to timing constraints, not bugs.")
    else:
        print(f"\n⚠️  Issues still exist in the business logic.")