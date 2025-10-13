import requests
import json

class RedfishClient:
    """
    A client for connecting to a Redfish service. Handles authentication (Basic or session) and provides
    an interface to retrieve Redfish resources as Python objects.
    """
    def __init__(self, base_url, username=None, password=None, use_session=True):
        # Ensure base URL is properly formatted (e.g., ends with /redfish/v1)
        base = base_url.rstrip('/')
        # Append /redfish/v1 if not already present
        # if not base.endswith('/redfish/v1'):
        #     if base.endswith('/redfish'):
        #         base = base + '/v1'
        #     else:
        #         base = base + '/redfish/v1'
        self.base_url = base
        self.username = username
        self.password = password
        self.use_session = use_session

        # Create a requests Session to persist settings (e.g., auth or headers)
        self._session = requests.Session()
        # (Optional) If needed, disable SSL verification for self-signed certs:
        self._session.verify = False

        # If using basic auth, set credentials for all requests
        if self.username is not None and self.password is not None:
            if not self.use_session:
                # Use HTTP Basic Auth for all requests
                self._session.auth = (self.username, self.password)

        # Variables to store session info if session auth is used
        self.session_token = None
        self.session_resource = None
        # Placeholder for the service root resource object (set after connect)
        self.root = None

    def login(self):
        """Authenticate with the Redfish service using a session. Acquire a session token for future requests."""
        if self.username is None or self.password is None:
            raise Exception("No credentials provided for login")
        # Prepare login payload
        payload = {"UserName": self.username, "Password": self.password}
        url = f"{self.base_url}/redfish/v1/SessionService/Sessions"
        # Use basic auth for this request (some services may allow session creation without it)
        response = self._session.post(url, json=payload, auth=(self.username, self.password))
        if response.status_code not in (200, 201):
            raise Exception(f"Redfish login failed: {response.status_code} - {response.text}")
        # On success, retrieve the token and session URI from headers
        token = response.headers.get("X-Auth-Token")
        session_location = response.headers.get("Location")
        if token:
            self.session_token = token
            # Include the token in default headers for subsequent requests
            self._session.headers.update({"X-Auth-Token": token})
        if session_location:
            # Construct full session resource URI if not already absolute
            if session_location.startswith("http"):
                self.session_resource = session_location
            else:
                self.session_resource = self.base_url.rstrip('/') + '/' + session_location.lstrip('/')
        # (Now self._session will use the X-Auth-Token for authenticated requests)

    def logout(self):
        """Log out of the Redfish session by deleting the session resource on the server."""
        if self.session_token and self.session_resource:
            resp = self._session.delete(self.session_resource)
            if resp.status_code not in (200, 204):
                raise Exception(f"Redfish logout failed: {resp.status_code} - {resp.text}")
        # Close the HTTP session
        self._session.close()
        # Clear session info
        self.session_token = None
        self.session_resource = None

    def get(self, path):
        """Send a GET request to the given Redfish path (relative or absolute) and return the JSON data."""
        url = path
        if not url.startswith("http"):
            url = self.base_url.rstrip('/') + '/' + path.lstrip('/')
        response = self._session.get(url)
        if response.status_code != 200:
            raise Exception(f"GET {url} failed: {response.status_code} - {response.text}")
        return response.json()

    def post(self, path, data=None):
        """Send a POST request to the given Redfish path with a JSON payload. Return response JSON (if any)."""
        url = path
        if not url.startswith("http"):
            url = self.base_url.rstrip('/') + '/' + path.lstrip('/')
        response = self._session.post(url, json=data or {})
        if response.status_code not in (200, 201, 204):
            raise Exception(f"POST {url} failed: {response.status_code} - {response.text}")
        # Return JSON if available
        try:
            return response.json()
        except ValueError:
            return None

    def patch(self, path, data):
        """Send a PATCH request to update the resource at the given path with the provided JSON fields."""
        url = path
        if not url.startswith("http"):
            url = self.base_url.rstrip('/') + '/' + path.lstrip('/')
        response = self._session.patch(url, json=data)
        if response.status_code not in (200, 204):
            raise Exception(f"PATCH {url} failed: {response.status_code} - {response.text}")
        return True  # success

    def delete(self, path):
        """Send a DELETE request to the given Redfish path to delete the resource."""
        url = path
        if not url.startswith("http"):
            url = self.base_url.rstrip('/') + '/' + path.lstrip('/')
        response = self._session.delete(url)
        if response.status_code not in (200, 204):
            raise Exception(f"DELETE {url} failed: {response.status_code} - {response.text}")
        return True

    def connect(self):
        """
        Connect to the Redfish service and fetch the service root.
        Returns a RedfishResource representing the service root for navigation.
        """
        # If using session-based auth and not yet logged in, do so now
        if self.username and self.password and self.use_session and self.session_token is None:
            self.login()
        # Fetch the service root resource (e.g. /redfish/v1/)
        root_data = self.get(self.base_url + '/redfish/v1/')
        # Wrap the root JSON in a RedfishResource object for easy navigation
        self.root = RedfishResource(self, data=root_data, path=self.base_url + '/redfish/v1/')
        return self.root

    def __getattr__(self, name):
        """
        Fallback attribute access: if attribute not found on client, try to get it from the service root.
        This allows `client.Systems` to work as a shorthand for `client.root.Systems`.
        """
        if self.root is None:
            # If not connected yet, do it now (this will handle authentication as needed)
            self.connect()
        return getattr(self.root, name)


class RedfishResource:
    """
    Represents a Redfish resource (single resource or a collection).
    Provides dynamic attribute access to properties and links, and generates methods for actions.
    """
    def __init__(self, client, data=None, path=None):
        self.client = client  # Reference to the RedfishClient
        # Load data, fetching from path if not provided
        if data is None:
            if path is None:
                raise ValueError("RedfishResource requires either data or path")
            data = self.client.get(path)
        self.data = data
        # Determine the resource's canonical path
        if path:
            self.path = path if path.startswith("http") else path  # store as given (could be relative or full URL)
        else:
            # If no path given, use @odata.id from data if available
            self.path = data.get('@odata.id')
        # Check if this is a collection (presence of "Members" list usually means a collection resource)
        self._is_collection = bool(self.data.get("Members"))

        # Dynamically create instance methods for any Actions exposed by this resource
        actions = self.data.get("Actions", {})
        for action_name, action_info in actions.items():
            if action_name == 'Oem':
                # OEM actions (nested under "Actions" -> "Oem")
                for oem_action_name, oem_action_info in action_info.items():
                    if oem_action_name.startswith("#"):
                        method = self._create_action_method(oem_action_name, oem_action_info)
                        # Bind method to this instance with a clean name (e.g. "DellReboot" from "#Dell.Reboot")
                        setattr(self, oem_action_name.lstrip('#').split('.')[-1], method)
            else:
                if action_name.startswith("#"):
                    method = self._create_action_method(action_name, action_info)
                    setattr(self, action_name.lstrip('#').split('.')[-1], method)

    def _create_action_method(self, action_name, action_info):
        """
        Helper to generate a callable method for a Redfish Action.
        Returns a MethodType bound to the resource instance.
        """
        target_url = action_info.get("target")
        def action_func(self, **payload):
            # Perform the action via POST to the action target.
            # If payload is empty, send an empty JSON object.
            return self.client.post(target_url, data=payload if payload else {})
        action_func.__name__ = action_name.lstrip('#').split('.')[-1]
        from types import MethodType
        return MethodType(action_func, self)

    def get(self):
        """Refresh this resource's data by GETting it again from the server."""
        new_data = self.client.get(self.path)
        self.data = new_data
        return self

    def patch(self, updates):
        """
        Update writable properties of this resource via HTTP PATCH.
        `updates` should be a dict of {property: new_value}.
        """
        success = self.client.patch(self.path, updates)
        if success:
            # Update local data cache with the new values
            self.data.update(updates)
        return success

    def delete(self):
        """Delete this resource from the server (if allowed)."""
        return self.client.delete(self.path)

    def create(self, new_data):
        """
        If this resource is a collection, create a new member by POSTing to it.
        Returns a RedfishResource for the newly created item.
        """
        if not self._is_collection:
            raise Exception("Cannot create on a non-collection resource")
        result = self.client.post(self.path, data=new_data)
        if result is None:
            # No JSON returned (perhaps got HTTP 204), try to retrieve via Location header if needed.
            raise Exception("Resource created, but no data returned")
        # If an @odata.id is present in result, use it; otherwise assume result is the resource body.
        new_path = result.get('@odata.id')
        return RedfishResource(self.client, data=result, path=new_path)

    def __getattr__(self, name):
        """
        Dynamic attribute access for resource properties:
         - If `name` is a key in the resource's JSON data:
            - If the value is a dict with '@odata.id', a linked sub-resource is fetched and returned as RedfishResource.
            - If the value is a list of links, returns a list of RedfishResource objects for each link.
            - Otherwise, returns the value (primitive or dict) directly.
        """
        if name in self.data:
            value = self.data[name]
            # If value is a nested resource link (dict with @odata.id), fetch that resource
            if isinstance(value, dict) and '@odata.id' in value:
                return RedfishResource(self.client, path=value['@odata.id'])
            # If value is a list, possibly a collection of links or embedded objects
            if isinstance(value, list):
                if value and isinstance(value[0], dict) and '@odata.id' in value[0]:
                    # List of resource links -> return list of resource objects
                    return [RedfishResource(self.client, path=item['@odata.id']) for item in value]
                else:
                    # List of primitive values or dicts without @odata.id
                    return value
            # If value is a dict without an @odata.id (embedded object), return it as-is (or could wrap in a helper object)
            return value
        # If not found in data, default behavior
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """
        Dynamic attribute setting for resource properties:
         - If setting a known property (exists in self.data), a PATCH request is sent to update the property on the server.
         - Otherwise, for internal attributes or unknown properties, normal attribute setting is performed.
        """
        # Internal attributes are set normally
        if name in ["client", "data", "path", "_is_collection"]:
            object.__setattr__(self, name, value)
        elif self.data is not None and name in self.data:
            # Attempt to update an existing resource property via PATCH
            updates = {name: value}
            success = self.client.patch(self.path, updates)
            if success:
                self.data[name] = value  # update local data on success
        else:
            # Fallback: not a known resource property, set as a regular attribute (perhaps used for caching, etc.)
            object.__setattr__(self, name, value)

    def __iter__(self):
        """
        If this resource is a collection, iterate over members by yielding RedfishResource for each member.
        Allows: `for item in resource: ...`
        """
        if not self._is_collection or "Members" not in self.data:
            raise TypeError(f"Resource at {self.path} is not a collection and cannot be iterated")
        for member in self.data["Members"]:
            if isinstance(member, dict) and "@odata.id" in member:
                yield RedfishResource(self.client, path=member["@odata.id"])
            else:
                # In case Members entries are not dicts (unusual in Redfish), yield raw
                yield member

    def __len__(self):
        """Return number of members if this resource is a collection."""
        if not self._is_collection or "Members" not in self.data:
            raise TypeError("Resource is not a collection")
        return len(self.data.get("Members", []))

    def __repr__(self):
        # Human-friendly representation: show type and identity
        res_type = self.data.get("@odata.type", "Resource")
        identifier = self.data.get("Id") or self.data.get("Name") or self.path
        return f"<RedfishResource {res_type} ({identifier})>"
