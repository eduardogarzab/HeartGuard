"""Test rápido para ver qué trae el endpoint de devices."""
import sys
sys.path.insert(0, ".")

from heartguard_tk.api.client import ApiClient

def main():
    client = ApiClient(base_url="http://136.115.53.140:8080")
    
    print("=" * 60)
    print("TEST: Devices Endpoint")
    print("=" * 60)
    
    # Login
    print("\n1. LOGIN...")
    try:
        login_response = client.login_patient("maria.delgado@patients.heartguard.com", "Paciente#2025")
        print(f"✅ Login: {login_response.full_name}")
        token = login_response.access_token
    except Exception as e:
        print(f"❌ Login FAILED: {e}")
        return
    
    # Devices
    print("\n2. DEVICES...")
    try:
        devices_response = client.get_patient_devices(token=token)
        print(f"✅ Devices Response Type: {type(devices_response)}")
        print(f"✅ Devices Response: {devices_response}")
        
        if isinstance(devices_response, dict):
            # Puede venir con wrapper "data" o directo
            if "data" in devices_response:
                data = devices_response["data"]
            else:
                data = devices_response
            
            items = data.get("items") or data.get("devices", [])
            print(f"\n📱 Total devices: {len(items)}")
            
            for idx, device in enumerate(items, 1):
                print(f"\n   Device {idx}:")
                print(f"      - Serial: {device.get('serial_number') or device.get('serial')}")
                print(f"      - Type: {device.get('device_type') or device.get('type')}")
                print(f"      - Status: {device.get('status')}")
                print(f"      - Brand: {device.get('brand')}")
                print(f"      - Model: {device.get('model')}")
                print(f"      - Last Activity: {device.get('last_activity')}")
    except Exception as e:
        print(f"❌ Devices FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
