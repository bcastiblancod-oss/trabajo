#!/usr/bin/env python3
"""
Debug specific failing test cases for Hotel API
"""
import requests
from datetime import datetime, date, timedelta
import json

def debug_reservation_issues():
    base_url = "https://boutique-reserve-hub.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as guest
    login_data = {"email": "huesped@test.com", "password": "Huesped123!"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("🔍 DEBUGGING RESERVATION MODIFICATION AND CANCELLATION\n")
    
    # Get available rooms
    tomorrow = date.today() + timedelta(days=1)
    checkout = date.today() + timedelta(days=3)
    
    params = {
        'fecha_checkin': tomorrow.isoformat(),
        'fecha_checkout': checkout.isoformat()
    }
    
    response = requests.get(f"{api_url}/habitaciones/disponibilidad", headers=headers, params=params)
    rooms = response.json()['habitaciones_disponibles']
    
    if not rooms:
        print("❌ No available rooms found")
        return
    
    room = rooms[0]
    print(f"✅ Selected room: {room['numero']} (Type: {room['tipo_habitacion']['nombre']})")
    
    # Create reservation
    reservation_data = {
        "habitacion_id": room['id'],
        "fecha_checkin": tomorrow.isoformat(),
        "fecha_checkout": checkout.isoformat(),
        "num_huespedes": 2,
        "huesped": {
            "nombre_completo": "Debug Test User",
            "documento": "DEBUG123",
            "email": "debug@test.com",
            "telefono": "3001234567",
            "ciudad": "Bogotá",
            "pais": "Colombia"
        },
        "metodo_pago": "efectivo"
    }
    
    response = requests.post(f"{api_url}/reservas", headers=headers, json=reservation_data)
    
    if response.status_code != 201:
        print(f"❌ Failed to create reservation: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    reservation = response.json()
    print(f"✅ Created reservation: {reservation['codigo']}")
    print(f"   Original price: ${reservation['precio_total']:,.0f}")
    print(f"   Check-in: {reservation['fecha_checkin']}")
    print(f"   Check-out: {reservation['fecha_checkout']}")
    
    # Debug 1: Try to modify reservation
    print(f"\n🔧 TESTING RESERVATION MODIFICATION")
    
    new_checkout = date.today() + timedelta(days=4)
    modify_data = {
        "fecha_checkout": new_checkout.isoformat(),
        "notas": "Debug modification test"
    }
    
    response = requests.put(f"{api_url}/reservas/{reservation['id']}", headers=headers, json=modify_data)
    
    print(f"   Modification Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error Response: {response.text}")
        try:
            error_data = response.json()
            print(f"   Error Detail: {error_data.get('detail', 'No details available')}")
        except:
            pass
    else:
        updated_res = response.json()
        print(f"   ✅ Successfully modified to: {updated_res['fecha_checkout']}")
    
    # Debug 2: Try to cancel reservation
    print(f"\n❌ TESTING RESERVATION CANCELLATION")
    
    cancel_data = {"motivo": "Debug cancellation test"}
    
    response = requests.post(f"{api_url}/reservas/{reservation['id']}/cancelar", headers=headers, json=cancel_data)
    
    print(f"   Cancellation Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error Response: {response.text}")
        try:
            error_data = response.json()
            print(f"   Error Detail: {error_data.get('detail', 'No details available')}")
        except:
            pass
    else:
        cancel_result = response.json()
        print(f"   Original Amount: ${cancel_result.get('monto_original', 0):,.0f}")
        print(f"   Refund Amount: ${cancel_result.get('monto_reembolso', 0):,.0f}")
        print(f"   Refund Percentage: {cancel_result.get('porcentaje_reembolso', 0)}%")
        print(f"   Policy Applied: {cancel_result.get('politica_aplicada', 'N/A')}")
        
        # Check timing
        now = datetime.now()
        checkin_dt = datetime.fromisoformat(reservation['fecha_checkin'].replace('Z', '+00:00'))
        hours_until = (checkin_dt.replace(tzinfo=None) - now).total_seconds() / 3600
        print(f"   Hours until check-in: {hours_until:.1f}")
    
    print(f"\n📝 SUMMARY:")
    print(f"   - Reservation created successfully ✅")
    print(f"   - Modification: {'✅' if response.status_code == 200 else '❌'}")
    print(f"   - Cancellation: {'✅' if 'monto_reembolso' in locals() and cancel_result.get('porcentaje_reembolso', 0) > 0 else '❌'}")


if __name__ == "__main__":
    debug_reservation_issues()