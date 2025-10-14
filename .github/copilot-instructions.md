# Copilot Project Instructions

Purpose: Enable AI coding agents to work productively on this Redfish dynamic client wrapper (`rackfish`). Keep responses focused on the concrete patterns implemented here rather than generic Redfish or Python advice.

## Big Picture
- This repo provides a lightweight dynamic Redfish API wrapper centered on two classes in `rackfish.py`: `RedfishClient` (HTTP/session handling + root navigation) and `RedfishResource` (lazy, dynamic object graph over Redfish JSON).
- Design goals: minimal dependencies (only `requests`), lazy fetching of linked resources, automatic mapping of JSON properties to Python attributes, treating Redfish Collections as iterable, and auto-generation + validation of Actions using associated `ActionInfo` metadata.
- Key paradigm: Access resources via attribute traversal (e.g. `client.Systems`), iterate collections, and invoke Actions as dynamically attached methods with parameter validation when `@Redfish.ActionInfo` is present.

## Core Files
- `rackfish.py`: Entire implementation + inline demo when run as `__main__`.
- `example.py`: Usage walkthrough (session login, traversing `Systems`, invoking `Reset`, creating accounts).
- `requirements.txt`: Only dependency is `requests`.

## Object Mapping Rules
- JSON keys that are valid Python identifiers become direct attributes on `RedfishResource` instances.
- Keys that are not valid identifiers remain in the internal `_raw` dict and are accessible via `resource["Some-Key"]`.
- Dict values:
  - If dict == `{ "@odata.id": "/path" }` -> becomes a lazy link stub (fetched on first attribute access or explicit method requiring data).
  - If dict contains `@odata.id` plus other fields -> also treated as lazy to prevent recursion depth issues during init.
- Lists are recursively converted element-wise (producing lists of primitives or `RedfishResource` objects).
- Collections are detected by presence of a top-level `Members` list; such resources become iterable and support `len()`.
- **OEM/Links Surfacing**: Child objects and properties from `Oem` (vendor extensions) and `Links` are automatically surfaced to the main object for convenient access, avoiding name collisions with existing attributes.
- **Recursion guard**: All nested resource objects defer hydration (`fetched=False`) to avoid stack overflow with deeply nested Redfish responses.

## Lazy Fetch Semantics
- A `RedfishResource` created as a link stub (only `@odata.id`) defers network retrieval until:
  - Any attribute (other than private) is accessed, or
  - Methods like `to_dict()`, iteration, or collection length are used.
- Internal `_ensure_fetched()` centralizes this logic; modifications must call it before relying on `_raw` content.

## Actions
- Redfish Actions under the `Actions` dict (including OEM nested under `Actions["Oem"][vendor]`) are bound as instance methods.
- Action method names are stripped of the leading hash and namespace prefix (example omitted to satisfy linter).
- If `@Redfish.ActionInfo` exists, its schema is fetched immediately to build a validator:
  - Validates required parameters, unknown parameters, basic data types (`String`, `Integer`, `Number`, `Boolean`, `Array`, `Object`, plus pass-through for `Password`/`Enumeration`) and `AllowableValues` membership.
  - A signature hint string is appended to the action method docstring.
- Allowable property values for writable attributes can be retrieved via `resource.get_allowable_values("PropertyName")`, which looks up `<PropertyName>@Redfish.AllowableValues`.

## PATCH / Mutations
- Simple primitive properties can be updated via attribute assignment: `system.AssetTag = "NewTag"` triggers a PATCH with `{ "AssetTag": "NewTag" }` if the original property was a non-container primitive.
- More complex updates (nested objects, lists) should use `resource.patch({...})` to ensure correct refresh.
- After a direct PATCH, `refresh()` re-fetches and re-hydrates attributes (used internally by `patch()` and some creation flows).

## Collections & CRUD
- Creating a resource within a collection: `new = accounts_collection.create({...})` sends POST to collection path.
- Return handling: If response body contains `@odata.id`, a fully fetched `RedfishResource` is returned; otherwise the collection is refreshed so caller can discover the new member.
- Deleting: `resource.delete()` calls HTTP DELETE; caller manages any references.

## HTTP / Auth
- `RedfishClient` normalizes `base_url` to ensure it ends with `/redfish/v1` (appends if missing).
- Session auth path: POST to `/SessionService/Sessions` storing `X-Auth-Token` + session URI; `logout()` attempts DELETE of session.
- If `use_session=False`, basic auth tuple is attached to the `requests.Session` and explicit `login()` is unnecessary.
- All methods use a common timeout (default 30s) and raise `RedfishError` on non-success responses or malformed JSON.

## Extension Guidelines (For AI Agents)
- When adding helpers, keep zero or minimal new dependencies; prefer standard library.
- Preserve lazy semantics: never force-fetch inside simple property introspection unless required (call `_ensure_fetched()` sparingly).
- For new validation logic or action enhancements, hook into `_compile_action_validator` rather than duplicating checks.
- If introducing caching beyond existing `_action_info_cache`, guard with the instance `_lock` in `RedfishClient` for thread safety.
- Maintain public surface simplicity: avoid requiring users to know internal `_raw` structure unless absolutely needed.
- **Recursion guard**: All nested resource objects defer hydration (`fetched=False`) to avoid stack overflow with deeply nested Redfish responses.

## Testing / Examples
- Use `example.py` as reference for constructing new higher-level examples or tests.
- For mock testing, consider injecting a fake `requests.Session` or wrapping `RedfishClient._http` methods; current design centralizes network calls in `RedfishClient.get/post/patch/delete`.

## Common Pitfalls
- Attempting to set complex/nested structures via direct attribute assignment will not PATCH; instruct users to call `.patch()`.
- Iterating a non-collection raises `TypeError`; ensure presence of `Members` in JSON before assuming iterability.
- Some BMCs may omit `ActionInfo`; action methods should still function without validation (validator is optional).

## Quick Usage Pattern
```python
client = RedfishClient("https://bmc", "user", "pass", use_session=True, verify_ssl=False)
root = client.connect()
for system in client.Systems:
    # Standard properties
    print(system.PowerState)
    
    # OEM properties surfaced automatically (e.g., Huawei.BootMode -> BootMode)
    if hasattr(system, "BootMode"):
        print(f"OEM Boot Mode: {system.BootMode}")
    
    # Links surfaced automatically (e.g., Links.Chassis -> Chassis)
    if hasattr(system, "Chassis"):
        for chassis in system.Chassis:
            print(f"Chassis: {chassis.Id}")
    
    # Actions (standard and OEM)
    if hasattr(system, "Reset"):
        system.Reset(ResetType="GracefulRestart")
client.logout()
```

---
Provide feedback if additional architecture details, contribution norms, or workflow steps should be captured.
