# rackfish Quick Start Guide

Get started with rackfish in 5 minutes!

## Installation

```bash
pip install rackfish
```

## Basic Usage

### 1. Connect to BMC

```python
from rackfish import RedfishClient

# Using session authentication (recommended)
client = RedfishClient(
    base_url="https://192.168.1.100",
    username="admin",
    password="password",
    use_session=True,
    verify_ssl=False  # For self-signed certificates
)

# Connect and login
root = client.connect()
```

### 2. Navigate Resources

```python
# Access systems
for system in client.Systems:
    print(f"System: {system.Id}")
    print(f"  Model: {system.Model}")
    print(f"  Power State: {system.PowerState}")
    print(f"  Health: {system.Status.Health}")
    print()
```

### 3. Perform Actions

```python
# Reset a system
system = client.Systems[0]  # Get first system
system.Reset(ResetType="GracefulRestart")

# Or force power off
system.Reset(ResetType="ForceOff")
```

### 4. Update Properties

```python
# Update simple property
system.AssetTag = "Server-001"

# For complex updates, use patch()
system.patch({
    "AssetTag": "Server-001",
    "IndicatorLED": "Lit"
})
```

### 5. Manage Users

```python
# Access account service
accounts = client.AccountService.Accounts

# Create new user
new_user = accounts.create({
    "UserName": "operator",
    "Password": "SecurePass123!",
    "RoleId": "Operator"
})

# List all users
for account in accounts:
    print(f"User: {account.UserName}, Role: {account.RoleId}")

# Delete user
account = accounts[2]  # Get specific account
account.delete()
```

### 6. Check System Health

```python
system = client.Systems[0]

# Overall health
print(f"System Health: {system.Status.Health}")
print(f"State: {system.Status.State}")

# Check temperatures
if hasattr(system, 'Thermal'):
    thermal = system.Thermal
    for temp in thermal.Temperatures:
        print(f"{temp.Name}: {temp.ReadingCelsius}°C (Status: {temp.Status.Health})")

# Check power supplies
if hasattr(system, 'Power'):
    power = system.Power
    for psu in power.PowerSupplies:
        print(f"{psu.Name}: {psu.PowerOutputWatts}W (Status: {psu.Status.Health})")
```

### 7. Configure Network

```python
# Access network interfaces
system = client.Systems[0]
for nic in system.EthernetInterfaces:
    print(f"NIC: {nic.Id}")
    print(f"  MAC: {nic.MACAddress}")
    print(f"  Speed: {nic.SpeedMbps} Mbps")
    
    # Configure static IP
    if hasattr(nic, 'IPv4Addresses'):
        nic.patch({
            "IPv4Addresses": [{
                "Address": "192.168.1.101",
                "SubnetMask": "255.255.255.0",
                "Gateway": "192.168.1.1",
                "AddressOrigin": "Static"
            }]
        })
```

### 8. Subscribe to Events

```python
# Create event subscription
subscriptions = client.EventService.Subscriptions

new_sub = subscriptions.create({
    "Destination": "https://myserver.com/events",
    "EventTypes": ["Alert", "StatusChange"],
    "Context": "MyApp",
    "Protocol": "Redfish"
})

print(f"Subscription created: {new_sub.Id}")
```

### 9. Access OEM Extensions

Vendor-specific properties are automatically surfaced:

```python
system = client.Systems[0]

# Huawei-specific properties (if available)
if hasattr(system, 'BootMode'):
    print(f"Boot Mode: {system.BootMode}")  # From Oem.Huawei.BootMode

# Dell-specific properties (if available)
if hasattr(system, 'ServerProfile'):
    print(f"Server Profile: {system.ServerProfile}")  # From Oem.Dell.ServerProfile
```

### 10. Cleanup

```python
# Always logout when done
client.logout()
```

## Common Patterns

### Error Handling

```python
from rackfish import RedfishClient, RedfishError

try:
    client = RedfishClient("https://bmc", "admin", "password")
    client.connect()
    
    system = client.Systems[0]
    system.Reset(ResetType="GracefulRestart")
    
except RedfishError as e:
    print(f"Redfish Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
finally:
    if client:
        client.logout()
```

### Context Manager (Auto-logout)

```python
from contextlib import contextmanager

@contextmanager
def redfish_session(url, user, password):
    client = RedfishClient(url, user, password, use_session=True)
    client.connect()
    try:
        yield client
    finally:
        client.logout()

# Usage
with redfish_session("https://bmc", "admin", "password") as client:
    system = client.Systems[0]
    print(f"Power: {system.PowerState}")
# Automatically logs out
```

### Checking Property Existence

```python
system = client.Systems[0]

# Safe way to check for optional properties
if hasattr(system, 'AssetTag'):
    print(f"Asset Tag: {system.AssetTag}")

# For nested properties
if hasattr(system, 'Status') and hasattr(system.Status, 'Health'):
    print(f"Health: {system.Status.Health}")
```

### Iterating Collections

```python
# Get collection length
num_systems = len(client.Systems)
print(f"Found {num_systems} systems")

# Index access
first_system = client.Systems[0]
second_system = client.Systems[1]

# Iterate all members
for system in client.Systems:
    print(system.Id)

# List comprehension
system_ids = [sys.Id for sys in client.Systems]
```

### Getting Allowable Values

```python
system = client.Systems[0]

# Get allowable values for an action parameter
if hasattr(system, 'Reset'):
    allowed_types = system.get_allowable_values('ResetType')
    print(f"Allowed reset types: {allowed_types}")
    
# Get allowable values for a property
if hasattr(system, 'IndicatorLED'):
    allowed_leds = system.get_allowable_values('IndicatorLED')
    print(f"Allowed LED states: {allowed_leds}")
```

## Next Steps

- 📖 **Full Examples**: See [examples/](examples/) directory
- 📚 **Documentation**: Check [docs/INDEX.md](docs/INDEX.md)
- 🧪 **Tests**: Browse [tests/](tests/) for more usage patterns
- 💡 **Use Cases**: See [docs/USE_CASES.md](docs/USE_CASES.md) for 150+ examples
- 🐛 **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/rackfish/issues)

## Tips & Best Practices

1. **Use session authentication** for better performance and security
2. **Disable SSL verification** only for testing (not production)
3. **Always logout** when done to free BMC resources
4. **Check hasattr()** before accessing optional properties
5. **Use patch()** for complex updates instead of individual assignments
6. **Handle RedfishError** exceptions for robust error handling
7. **Read ActionInfo** to see required/optional parameters for actions

## Getting Help

- Check [EXAMPLES.md](docs/EXAMPLES.md) for comprehensive examples
- Read the [API documentation](docs/) 
- Open an issue on GitHub
- Review test files for usage patterns

Happy coding! 🚀
