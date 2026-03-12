#!/usr/bin/env python3
"""
Backend API Tests for Hotel Boutique Reservation System
Tests all key features: Authentication, RBAC, Rooms, Reservations, Check-in/out
"""
import requests
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Any
import json

class HotelAPITester:
    def __init__(self, base_url: str = "https://boutique-reserve-hub.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        
        # Test credentials
        self.test_users = {
            "admin": {"email": "admin@hotelimperium.com", "password": "Admin123!"},
            "recepcion": {"email": "recepcion@hotelimperium.com", "password": "Recep123!"},
            "huesped": {"email": "huesped@test.com", "password": "Huesped123!"}
        }
        
        self.tokens = {}
        self.test_data = {}
        
        # Test stats
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success:
            self.tests_passed += 1
            print(f"{status} - {name}")
        else:
            print(f"{status} - {name}: {details}")
            self.failed_tests.append({"name": name, "details": details})

    def make_request(self, method: str, endpoint: str, token: str = None, 
                    data: dict = None, params: dict = None) -> tuple[bool, dict, int]:
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"raw_response": response.text}
            
            return response.ok, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    # ============== AUTHENTICATION TESTS ==============
    def test_health_check(self):
        """Test health check endpoint"""
        success, data, status = self.make_request('GET', '/health')
        self.log_test(
            "Health Check",
            success and status == 200,
            f"Status: {status}, Response: {data}"
        )
        return success

    def test_login_all_users(self):
        """Test login for all user types"""
        for role, credentials in self.test_users.items():
            success, data, status = self.make_request('POST', '/auth/login', data=credentials)
            
            if success and 'access_token' in data:
                self.tokens[role] = data['access_token']
                user_data = data.get('usuario', {})
                expected_role = "administrador" if role == "admin" else ("recepcionista" if role == "recepcion" else "huesped")
                
                role_correct = user_data.get('rol') == expected_role
                self.log_test(
                    f"Login {role.upper()}",
                    role_correct,
                    f"Expected role: {expected_role}, Got: {user_data.get('rol')}"
                )
            else:
                self.log_test(f"Login {role.upper()}", False, f"Status: {status}, Data: {data}")
        
        return len(self.tokens) == 3

    def test_get_current_user(self):
        """Test /auth/me endpoint for each user"""
        for role, token in self.tokens.items():
            success, data, status = self.make_request('GET', '/auth/me', token=token)
            self.log_test(
                f"Get Current User ({role.upper()})",
                success and 'email' in data,
                f"Status: {status}"
            )

    # ============== ROOM MANAGEMENT TESTS ==============
    def test_list_rooms(self):
        """Test listing rooms (all authenticated users can access)"""
        for role, token in self.tokens.items():
            success, data, status = self.make_request('GET', '/habitaciones', token=token)
            
            if success and isinstance(data, list):
                room_count = len(data)
                self.log_test(
                    f"List Rooms ({role.upper()})",
                    room_count >= 24,  # Should have 24 pre-loaded rooms
                    f"Expected ≥24 rooms, Got: {room_count}"
                )
                
                # Store room data for later tests
                if role == 'admin' and data:
                    self.test_data['rooms'] = data
                    self.test_data['sample_room'] = data[0]
            else:
                self.log_test(f"List Rooms ({role.upper()})", False, f"Status: {status}, Data: {data}")

    def test_room_types(self):
        """Test getting room types"""
        success, data, status = self.make_request('GET', '/habitaciones/tipos', token=self.tokens['admin'])
        
        if success and isinstance(data, list):
            type_count = len(data)
            expected_types = {'Estándar', 'Suite', 'Familiar'}
            found_types = {t.get('nombre') for t in data}
            
            self.log_test(
                "Room Types",
                expected_types.issubset(found_types),
                f"Expected types: {expected_types}, Found: {found_types}"
            )
            self.test_data['room_types'] = data
        else:
            self.log_test("Room Types", False, f"Status: {status}")

    def test_availability_query(self):
        """RF-01: Test room availability query with filters"""
        tomorrow = date.today() + timedelta(days=1)
        day_after = date.today() + timedelta(days=3)
        
        params = {
            'fecha_checkin': tomorrow.isoformat(),
            'fecha_checkout': day_after.isoformat(),
            'num_huespedes': 2,
            'precio_min': 100000,
            'precio_max': 400000
        }
        
        success, data, status = self.make_request(
            'GET', '/habitaciones/disponibilidad', 
            token=self.tokens['huesped'], 
            params=params
        )
        
        if success and 'habitaciones_disponibles' in data:
            available_count = len(data['habitaciones_disponibles'])
            self.log_test(
                "RF-01: Availability Query",
                available_count > 0,
                f"Available rooms: {available_count}, Total: {data.get('total', 0)}"
            )
            self.test_data['available_rooms'] = data['habitaciones_disponibles']
        else:
            self.log_test("RF-01: Availability Query", False, f"Status: {status}, Data: {data}")

    # ============== RESERVATION TESTS ==============
    def test_create_reservation(self):
        """RF-02: Test reservation creation with unique code and price calculation"""
        if not self.test_data.get('available_rooms'):
            self.log_test("RF-02: Create Reservation", False, "No available rooms found")
            return

        room = self.test_data['available_rooms'][0]
        tomorrow = date.today() + timedelta(days=1)
        checkout = date.today() + timedelta(days=3)
        
        reservation_data = {
            "habitacion_id": room['id'],
            "fecha_checkin": tomorrow.isoformat(),
            "fecha_checkout": checkout.isoformat(),
            "num_huespedes": 2,
            "huesped": {
                "nombre_completo": "Juan Test Usuario",
                "documento": "12345678",
                "email": "juan.test@email.com",
                "telefono": "3001234567",
                "direccion": "Calle 123",
                "ciudad": "Bogotá",
                "pais": "Colombia"
            },
            "acompanantes": [],
            "servicios_adicionales": [],
            "metodo_pago": "tarjeta_credito",
            "notas": "Reserva de prueba"
        }
        
        success, data, status = self.make_request(
            'POST', '/reservas', 
            token=self.tokens['huesped'], 
            data=reservation_data
        )
        
        if success and 'codigo' in data:
            self.log_test(
                "RF-02: Create Reservation",
                'precio_total' in data and data.get('codigo', '').startswith('RES-'),
                f"Code: {data.get('codigo')}, Total: {data.get('precio_total')}"
            )
            self.test_data['reservation'] = data
        else:
            self.log_test("RF-02: Create Reservation", False, f"Status: {status}, Data: {data}")

    def test_modify_reservation(self):
        """RF-03: Test reservation modification (only >24h in advance)"""
        if not self.test_data.get('reservation'):
            self.log_test("RF-03: Modify Reservation", False, "No reservation to modify")
            return

        reservation_id = self.test_data['reservation']['id']
        
        # Try to modify checkout date
        new_checkout = date.today() + timedelta(days=4)
        modify_data = {
            "fecha_checkout": new_checkout.isoformat(),
            "notas": "Modificación de prueba - extendida un día"
        }
        
        success, data, status = self.make_request(
            'PUT', f'/reservas/{reservation_id}', 
            token=self.tokens['huesped'], 
            data=modify_data
        )
        
        self.log_test(
            "RF-03: Modify Reservation",
            success and data.get('fecha_checkout') == new_checkout.isoformat(),
            f"Status: {status}, New checkout: {data.get('fecha_checkout') if success else 'N/A'}"
        )

    def test_cancel_reservation(self):
        """RF-04: Test reservation cancellation with refund policy"""
        if not self.test_data.get('reservation'):
            self.log_test("RF-04: Cancel Reservation", False, "No reservation to cancel")
            return

        reservation_id = self.test_data['reservation']['id']
        
        cancel_data = {
            "motivo": "Prueba de cancelación con política de reembolso"
        }
        
        success, data, status = self.make_request(
            'POST', f'/reservas/{reservation_id}/cancelar', 
            token=self.tokens['huesped'], 
            data=cancel_data
        )
        
        if success and 'monto_reembolso' in data:
            # Since we're canceling >48h in advance, should get 100% refund
            original = data.get('monto_original', 0)
            refund = data.get('monto_reembolso', 0)
            percentage = data.get('porcentaje_reembolso', 0)
            
            self.log_test(
                "RF-04: Cancel Reservation",
                percentage == 100.0,
                f"Original: {original}, Refund: {refund} ({percentage}%)"
            )
        else:
            self.log_test("RF-04: Cancel Reservation", False, f"Status: {status}, Data: {data}")

    def test_reservation_search(self):
        """Test reservation search by different criteria"""
        # Create a new reservation first for testing search
        if not self.test_data.get('available_rooms'):
            self.log_test("Reservation Search", False, "No available rooms")
            return

        # Create reservation for search test
        room = self.test_data['available_rooms'][0]
        tomorrow = date.today() + timedelta(days=5)  # Different dates to avoid conflicts
        checkout = date.today() + timedelta(days=7)
        
        search_reservation = {
            "habitacion_id": room['id'],
            "fecha_checkin": tomorrow.isoformat(),
            "fecha_checkout": checkout.isoformat(),
            "num_huespedes": 1,
            "huesped": {
                "nombre_completo": "Maria Search Test",
                "documento": "87654321",
                "email": "maria.search@email.com",
                "telefono": "3009876543",
                "ciudad": "Medellín",
                "pais": "Colombia"
            },
            "metodo_pago": "efectivo"
        }
        
        success, data, status = self.make_request(
            'POST', '/reservas', 
            token=self.tokens['huesped'], 
            data=search_reservation
        )
        
        if not success:
            self.log_test("Reservation Search Setup", False, f"Failed to create search reservation")
            return

        search_code = data.get('codigo')
        
        # Test search by reservation code
        params = {'codigo': search_code}
        success, search_data, status = self.make_request(
            'GET', '/reservas/buscar', 
            token=self.tokens['recepcion'], 
            params=params
        )
        
        self.log_test(
            "Search by Code",
            success and len(search_data) > 0,
            f"Found {len(search_data) if success else 0} reservations with code {search_code}"
        )

    # ============== CHECK-IN/CHECK-OUT TESTS ==============
    def test_checkin_process(self):
        """RF-06: Test check-in process"""
        # First create a reservation for today's check-in
        if not self.test_data.get('available_rooms'):
            self.log_test("RF-06: Check-in Process", False, "No available rooms")
            return

        room = self.test_data['available_rooms'][0]
        today = date.today()
        checkout = date.today() + timedelta(days=2)
        
        checkin_reservation = {
            "habitacion_id": room['id'],
            "fecha_checkin": today.isoformat(),
            "fecha_checkout": checkout.isoformat(),
            "num_huespedes": 2,
            "huesped": {
                "nombre_completo": "Carlos Checkin Test",
                "documento": "11223344",
                "email": "carlos.checkin@email.com",
                "telefono": "3001122334",
                "ciudad": "Cali",
                "pais": "Colombia"
            },
            "metodo_pago": "tarjeta_debito"
        }
        
        # Create reservation
        success, res_data, status = self.make_request(
            'POST', '/reservas', 
            token=self.tokens['admin'], 
            data=checkin_reservation
        )
        
        if not success:
            self.log_test("RF-06: Check-in Setup", False, "Failed to create reservation for check-in")
            return

        # Process check-in
        checkin_data = {
            "reserva_id": res_data['id']
        }
        
        success, data, status = self.make_request(
            'POST', '/checkin', 
            token=self.tokens['recepcion'], 
            data=checkin_data
        )
        
        if success and 'reserva' in data:
            reserva_estado = data['reserva'].get('estado')
            self.log_test(
                "RF-06: Check-in Process",
                reserva_estado == 'checked_in',
                f"Reservation state: {reserva_estado}"
            )
            self.test_data['checkin'] = data
        else:
            self.log_test("RF-06: Check-in Process", False, f"Status: {status}, Data: {data}")

    def test_add_consumption(self):
        """Test adding consumption to checked-in reservation"""
        if not self.test_data.get('checkin'):
            self.log_test("Add Consumption", False, "No checked-in reservation")
            return

        reserva_id = self.test_data['checkin']['reserva_id']
        
        consumption = {
            "reserva_id": reserva_id,
            "descripcion": "Agua mineral x2",
            "cantidad": 2,
            "precio_unitario": 8000.0,
            "categoria": "minibar"
        }
        
        success, data, status = self.make_request(
            'POST', '/consumos', 
            token=self.tokens['recepcion'], 
            data=consumption
        )
        
        self.log_test(
            "Add Consumption",
            success and data.get('subtotal') == 16000.0,
            f"Status: {status}, Subtotal: {data.get('subtotal') if success else 'N/A'}"
        )

    def test_checkout_process(self):
        """RF-07: Test check-out process with invoice generation"""
        if not self.test_data.get('checkin'):
            self.log_test("RF-07: Check-out Process", False, "No checked-in reservation")
            return

        reserva_id = self.test_data['checkin']['reserva_id']
        
        checkout_data = {
            "reserva_id": reserva_id,
            "notas": "Check-out de prueba - todo en orden"
        }
        
        success, data, status = self.make_request(
            'POST', '/checkout', 
            token=self.tokens['recepcion'], 
            data=checkout_data
        )
        
        if success and 'factura_id' in data:
            total = data.get('total', 0)
            impuestos = data.get('impuestos', 0)
            
            self.log_test(
                "RF-07: Check-out Process",
                total > 0 and impuestos > 0,
                f"Total: {total}, Taxes: {impuestos}, Invoice: {data.get('factura_id')}"
            )
        else:
            self.log_test("RF-07: Check-out Process", False, f"Status: {status}, Data: {data}")

    # ============== RBAC TESTS ==============
    def test_rbac_permissions(self):
        """Test Role-Based Access Control"""
        
        # Test: Guest trying to create room (should fail)
        room_data = {
            "numero": "999",
            "piso": 9,
            "tipo_habitacion_id": self.test_data.get('room_types', [{}])[0].get('id', 'test'),
            "descripcion": "Test room"
        }
        
        success, data, status = self.make_request(
            'POST', '/habitaciones', 
            token=self.tokens['huesped'], 
            data=room_data
        )
        
        self.log_test(
            "RBAC: Guest Cannot Create Room",
            not success and status == 403,
            f"Status: {status} (should be 403)"
        )
        
        # Test: Receptionist can access all reservations
        success, data, status = self.make_request('GET', '/reservas', token=self.tokens['recepcion'])
        
        self.log_test(
            "RBAC: Receptionist Access All Reservations",
            success,
            f"Status: {status}"
        )
        
        # Test: Guest can only see their own reservations (already covered in reservation tests)

    # ============== EDGE CASES AND ERROR HANDLING ==============
    def test_invalid_dates(self):
        """Test validation for invalid dates"""
        if not self.test_data.get('available_rooms'):
            return

        room = self.test_data['available_rooms'][0]
        
        # Test: Past check-in date
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)
        
        invalid_reservation = {
            "habitacion_id": room['id'],
            "fecha_checkin": yesterday.isoformat(),
            "fecha_checkout": tomorrow.isoformat(),
            "num_huespedes": 1,
            "huesped": {
                "nombre_completo": "Invalid Date Test",
                "documento": "99999999",
                "email": "invalid@test.com",
                "telefono": "3009999999"
            },
            "metodo_pago": "efectivo"
        }
        
        success, data, status = self.make_request(
            'POST', '/reservas', 
            token=self.tokens['huesped'], 
            data=invalid_reservation
        )
        
        self.log_test(
            "Invalid Past Check-in Date",
            not success and status == 400,
            f"Status: {status} (should be 400)"
        )

    def test_room_capacity_validation(self):
        """Test room capacity validation"""
        if not self.test_data.get('available_rooms'):
            return

        # Find a room and exceed its capacity
        room = None
        for r in self.test_data['available_rooms']:
            if r.get('tipo_habitacion') and r['tipo_habitacion'].get('capacidad_maxima'):
                room = r
                break
        
        if not room:
            return

        max_capacity = room['tipo_habitacion']['capacidad_maxima']
        tomorrow = date.today() + timedelta(days=1)
        checkout = date.today() + timedelta(days=2)
        
        over_capacity_reservation = {
            "habitacion_id": room['id'],
            "fecha_checkin": tomorrow.isoformat(),
            "fecha_checkout": checkout.isoformat(),
            "num_huespedes": max_capacity + 1,  # Exceed capacity
            "huesped": {
                "nombre_completo": "Over Capacity Test",
                "documento": "88888888",
                "email": "overcapacity@test.com",
                "telefono": "3008888888"
            },
            "metodo_pago": "efectivo"
        }
        
        success, data, status = self.make_request(
            'POST', '/reservas', 
            token=self.tokens['huesped'], 
            data=over_capacity_reservation
        )
        
        self.log_test(
            "Room Capacity Validation",
            not success and status == 400,
            f"Status: {status}, Max capacity: {max_capacity}, Tried: {max_capacity + 1}"
        )

    # ============== MAIN TEST RUNNER ==============
    def run_all_tests(self):
        """Run all test suites"""
        print("🏨 Hotel Boutique API Testing Started")
        print("=" * 60)
        
        # Health and connectivity
        print("\n📡 CONNECTIVITY TESTS")
        self.test_health_check()
        
        # Authentication
        print("\n🔐 AUTHENTICATION TESTS")
        if not self.test_login_all_users():
            print("❌ Authentication failed - stopping tests")
            return self.get_results()
        
        self.test_get_current_user()
        
        # Room management
        print("\n🏠 ROOM MANAGEMENT TESTS")
        self.test_list_rooms()
        self.test_room_types()
        self.test_availability_query()
        
        # Reservations
        print("\n📅 RESERVATION TESTS")
        self.test_create_reservation()
        self.test_modify_reservation()
        self.test_cancel_reservation()
        self.test_reservation_search()
        
        # Check-in/Check-out
        print("\n🚪 CHECK-IN/CHECK-OUT TESTS")
        self.test_checkin_process()
        self.test_add_consumption()
        self.test_checkout_process()
        
        # Security and RBAC
        print("\n🔒 SECURITY & RBAC TESTS")
        self.test_rbac_permissions()
        
        # Edge cases
        print("\n⚠️  VALIDATION TESTS")
        self.test_invalid_dates()
        self.test_room_capacity_validation()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"\n{'=' * 60}")
        print(f"🏨 HOTEL BOUTIQUE API TEST RESULTS")
        print(f"{'=' * 60}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}")
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failed in enumerate(self.failed_tests, 1):
                print(f"  {i}. {failed['name']}: {failed['details']}")
        
        return {
            "success_rate": success_rate,
            "tests_passed": self.tests_passed,
            "tests_failed": len(self.failed_tests),
            "total_tests": self.tests_run,
            "failed_tests": self.failed_tests,
            "overall_success": success_rate >= 80  # 80% success threshold
        }


def main():
    """Main test execution"""
    print("Starting Hotel Boutique API Backend Tests...")
    
    tester = HotelAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())