# demo_scim_server.py - SCIM 2.0 Server with Entitlements Demo
# Repository: https://github.com/joevanhorn/api-entitlements-demo

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import re
import os

app = Flask(__name__)

# --- BEGIN AUTH MIDDLEWARE (Basic + Bearer) ---
import os
from base64 import b64decode
from flask import request, jsonify

# env-driven secrets
_EXPECTED_BEARER = os.environ.get("SCIM_AUTH_TOKEN", "").strip()
_BASIC_USER = os.environ.get("SCIM_BASIC_USER", "").strip()
_BASIC_PASS = os.environ.get("SCIM_BASIC_PASS", "").strip()

# paths that remain unauthenticated
_EXEMPT = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/scim/v2/ServiceProviderConfig"),
}

def _bearer_ok(h: str) -> bool:
    if not _EXPECTED_BEARER:
        return False
    if not h or not h.startswith("Bearer "):
        return False
    token = h.split(None, 1)[1].strip()
    return token == _EXPECTED_BEARER

def _basic_ok(h: str) -> bool:
    if not (_BASIC_USER and _BASIC_PASS):
        return False
    if not h or not h.startswith("Basic "):
        return False
    try:
        raw = b64decode(h.split(None, 1)[1]).decode("utf-8", "ignore")
    except Exception:
        return False
    if ":" not in raw:
        return False
    u, p = raw.split(":", 1)
    return (u == _BASIC_USER) and (p == _BASIC_PASS)

@app.before_request
def _require_auth_for_scim():
    key = (request.method.upper(), request.path)
    if key in _EXEMPT:
        return  # allow unauthenticated

    if request.path.startswith("/scim/v2/"):
        auth = request.headers.get("Authorization", "")
        if _bearer_ok(auth) or _basic_ok(auth):
            return  # authorized
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Unauthorized - Invalid or missing credentials",
            "status": "401",
        }), 401
# --- END AUTH MIDDLEWARE ---


# In-memory storage - simulates your cloud application's database
users_db = {}
entitlements_db = {
    "role_admin": {
        "id": "role_admin",
        "name": "Administrator",
        "description": "Full system access",
        "permissions": ["read", "write", "delete", "admin", "manage_users"]
    },
    "role_user": {
        "id": "role_user",
        "name": "Standard User",
        "description": "Basic access",
        "permissions": ["read", "write"]
    },
    "role_readonly": {
        "id": "role_readonly",
        "name": "Read Only",
        "description": "View only access",
        "permissions": ["read"]
    },
    "role_support": {
        "id": "role_support",
        "name": "Support Agent",
        "description": "Customer support access",
        "permissions": ["read", "write", "support", "view_tickets"]
    },
    "role_billing": {
        "id": "role_billing",
        "name": "Billing Manager",
        "description": "Billing and payment access",
        "permissions": ["read", "billing", "invoices", "payments"]
    }
}

# Activity log for dashboard
activity_log = []

def log_activity(action, details):
    """Log activities for the dashboard"""
    activity_log.insert(0, {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "details": details
    })
    if len(activity_log) > 100:
        activity_log.pop()

def simulate_cloud_app_call(operation, data):
    """Simulate calling your cloud app's API"""
    print(f"\n{'='*70}")
    print(f"🔌 SIMULATED CLOUD APP API CALL")
    print(f"{'='*70}")
    print(f"   Operation: {operation}")
    print(f"   Data: {json.dumps(data, indent=6)}")
    print(f"   [In production, this would call your actual cloud app's API]")
    print(f"{'='*70}\n")
    return {"success": True, "message": "Operation completed"}

# Dashboard HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Entitlements Demo - Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
        .header p { color: #666; font-size: 14px; line-height: 1.6; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); }
        .stat-card h3 {
            color: #667eea;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }
        .section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            font-size: 20px;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #f8f9fa;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
            font-size: 13px;
            text-transform: uppercase;
        }
        td {
            padding: 15px 12px;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
        }
        tr:hover { background: #f8f9fa; }
        code {
            background: #f1f3f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-active { background: #d4edda; color: #155724; }
        .badge-inactive { background: #f8d7da; color: #721c24; }
        .badge-role { background: #cce5ff; color: #004085; margin: 2px; }
        .badge-permission { background: #e7f3ff; color: #0066cc; margin: 2px; font-size: 10px; }
        .activity-item {
            padding: 15px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
            margin-bottom: 12px;
            border-radius: 4px;
        }
        .activity-item .time { font-size: 11px; color: #666; margin-bottom: 5px; font-weight: 600; }
        .activity-item .action { font-weight: 600; color: #333; margin-bottom: 5px; font-size: 14px; }
        .activity-item .details { font-size: 13px; color: #666; line-height: 1.5; }
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .info-box strong { color: #1976D2; }
        .info-box p { margin: 8px 0; line-height: 1.6; }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 13px;
        }
        .footer a { color: white; text-decoration: underline; }
        @media (max-width: 768px) {
            .stats { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 API Entitlements Demo Dashboard</h1>
            <p><strong>Repository:</strong> <a href="https://github.com/joevanhorn/api-entitlements-demo" target="_blank">joevanhorn/api-entitlements-demo</a></p>
            <p>This dashboard simulates your cloud application's state. In production, this data would come from your actual app's database via API calls.</p>
        </div>

        <div class="info-box">
            <strong>💡 How This Works:</strong>
            <p>• <strong>Okta discovers roles</strong> from the /AppRoles endpoint</p>
            <p>• <strong>Administrators assign users</strong> with specific roles in Okta</p>
            <p>• <strong>SCIM connector receives requests</strong> and would call your cloud app's API</p>
            <p>• <strong>Dashboard shows results</strong> as if they came from your real application</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="number">{{ users|length }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Users</h3>
                <div class="number">{{ active_users }}</div>
            </div>
            <div class="stat-card">
                <h3>Available Roles</h3>
                <div class="number">{{ roles|length }}</div>
            </div>
            <div class="stat-card">
                <h3>API Calls Logged</h3>
                <div class="number">{{ activities|length }}</div>
            </div>
        </div>

        <div class="section">
            <h2>👥 Provisioned Users</h2>
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Assigned Roles</th>
                        <th>Provisioned</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td><code>{{ user.id }}</code></td>
                        <td>{{ user.userName }}</td>
                        <td>{{ user.name.givenName }} {{ user.name.familyName }}</td>
                        <td>
                            {% if user.active %}
                            <span class="badge badge-active">Active</span>
                            {% else %}
                            <span class="badge badge-inactive">Inactive</span>
                            {% endif %}
                        </td>
                        <td>
                            {% for role in user.roles %}
                            <span class="badge badge-role">{{ role.display }}</span>
                            {% endfor %}
                            {% if not user.roles %}
                            <span style="color: #999; font-size: 12px;">No roles assigned</span>
                            {% endif %}
                        </td>
                        <td style="font-size: 12px;">{{ user.created[:10] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <p style="font-size: 16px; margin-bottom: 10px;">No users provisioned yet</p>
                <p>Assign a user in Okta to see them appear here!</p>
            </div>
            {% endif %}
        </div>

        <div class="section">
            <h2>🎭 Available Roles (Entitlements)</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 150px;">Role ID</th>
                        <th style="width: 200px;">Display Name</th>
                        <th>Description</th>
                        <th>Permissions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for role in roles %}
                    <tr>
                        <td><code>{{ role.id }}</code></td>
                        <td><strong>{{ role.name }}</strong></td>
                        <td>{{ role.description }}</td>
                        <td>
                            {% for perm in role.permissions %}
                            <span class="badge badge-permission">{{ perm }}</span>
                            {% endfor %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📊 Recent Activity Log</h2>
            {% if activities %}
                {% for activity in activities[:15] %}
                <div class="activity-item">
                    <div class="time">{{ activity.timestamp[:19].replace('T', ' ') }} UTC</div>
                    <div class="action">{{ activity.action }}</div>
                    <div class="details">{{ activity.details }}</div>
                </div>
                {% endfor %}
            {% else %}
            <div class="empty-state">
                <p style="font-size: 16px; margin-bottom: 10px;">No activity yet</p>
                <p>Start provisioning users from Okta to see activity!</p>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            🔄 Dashboard auto-refreshes every 5 seconds | 
            <a href="/scim/v2/Users">View SCIM Users</a> | 
            <a href="/scim/v2/AppRoles">View SCIM Roles</a> |
            <a href="/health">Health Check</a>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Interactive dashboard showing the simulated application state"""
    active_users = sum(1 for u in users_db.values() if u.get('active', True))
    
    return render_template_string(
        DASHBOARD_HTML,
        users=list(users_db.values()),
        roles=list(entitlements_db.values()),
        activities=activity_log,
        active_users=active_users
    )

@app.route('/scim/v2/ServiceProviderConfig', methods=['GET'])
def service_provider_config():
    """Service provider configuration"""
    log_activity("Config Request", "Okta requested service provider configuration")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "documentationUri": "https://github.com/joevanhorn/api-entitlements-demo",
        "patch": {"supported": True},
        "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter": {"supported": True, "maxResults": 200},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication using OAuth Bearer Token"
            }
        ]
    })

@app.route('/scim/v2/ResourceTypes', methods=['GET'])
def get_resource_types():
    """Resource types discovery"""
    
    log_activity("Resource Discovery", "Okta discovered available resource types")
    print("\n📋 Okta is discovering resource types...")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
        "totalResults": 2,
        "Resources": [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "User Account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                "schemaExtensions": [],
                "meta": {"resourceType": "ResourceType"}
            },
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "AppRole",
                "name": "AppRole",
                "endpoint": "/AppRoles",
                "description": "Application Roles (Entitlements)",
                "schema": "urn:okta:scim:schemas:core:1.0:Entitlement",
                "schemaExtensions": [],
                "meta": {"resourceType": "ResourceType"}
            }
        ]
    })

@app.route('/scim/v2/Schemas', methods=['GET'])
def get_schemas():
    """Schemas endpoint"""
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "Resources": []
    })

@app.route('/scim/v2/AppRoles', methods=['GET'])
def get_app_roles():
    """List all available application roles"""
    
    log_activity(
        "Entitlement Discovery",
        f"Okta discovered {len(entitlements_db)} available roles"
    )
    
    print(f"\n🎭 Okta is discovering {len(entitlements_db)} available roles...")
    simulate_cloud_app_call("GET /api/roles", {})
    
    roles = [
        {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            "id": role["id"],
            "displayName": role["name"],
            "value": role["id"],
            "description": role["description"],
            "meta": {"resourceType": "Entitlement"}
        }
        for role in entitlements_db.values()
    ]
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(roles),
        "startIndex": 1,
        "itemsPerPage": len(roles),
        "Resources": roles
    })

@app.route('/scim/v2/Users', methods=['POST'])
def create_user():
    """Create a new user"""
    
    data = request.json
    user_id = f"user_{len(users_db) + 1}"
    username = data.get('userName')
    roles = data.get('roles', [])
    
    role_names = [r.get('display', r.get('value')) for r in roles]
    log_activity("User Created", f"Created user {username} with roles: {', '.join(role_names) if role_names else 'None'}")
    
    print(f"\n{'='*70}")
    print(f"👤 CREATING USER: {username}")
    print(f"{'='*70}")
    
    simulate_cloud_app_call("POST /api/users", {
        "email": username,
        "roles": [r.get('value') for r in roles]
    })
    
    user = {
        "id": user_id,
        "userName": username,
        "name": data.get("name", {}),
        "emails": data.get("emails", []),
        "active": data.get("active", True),
        "roles": roles,
        "created": datetime.utcnow().isoformat() + "Z"
    }
    
    users_db[user_id] = user
    print(f"   ✅ User created with ID: {user_id}")
    print(f"{'='*70}\n")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user["roles"],
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["created"]
        }
    }), 201

@app.route('/scim/v2/Users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Retrieve a specific user"""
    
    user = users_db.get(user_id)
    if not user:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    simulate_cloud_app_call("GET /api/users/{id}", {"user_id": user_id})
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user.get("roles", []),
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user.get("modified", user["created"])
        }
    })

@app.route('/scim/v2/Users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Full update of a user"""
    
    user = users_db.get(user_id)
    if not user:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    data = request.json
    simulate_cloud_app_call("PUT /api/users/{id}", {"user_id": user_id, "data": data})
    
    user.update({
        "userName": data.get("userName", user["userName"]),
        "name": data.get("name", user["name"]),
        "emails": data.get("emails", user["emails"]),
        "active": data.get("active", user["active"]),
        "roles": data.get("roles", user.get("roles", [])),
        "modified": datetime.utcnow().isoformat() + "Z"
    })
    
    log_activity("User Updated", f"Updated user {user['userName']} via PUT")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user.get("roles", []),
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["modified"]
        }
    })

@app.route('/scim/v2/Users/<user_id>', methods=['PATCH'])
def patch_user(user_id):
    """Partial update of a user"""
    
    print(f"\n{'='*70}")
    print(f"🔧 PATCHING USER: {user_id}")
    print(f"{'='*70}")
    
    user = users_db.get(user_id)
    if not user:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    data = request.json
    changes = []
    
    for operation in data.get('Operations', []):
        op = operation['op'].lower()
        value = operation.get('value', {})
        path = operation.get('path', '')
        
        if op == 'add' and 'roles' in value:
            new_roles = value['roles']
            for role in new_roles:
                simulate_cloud_app_call("POST /api/users/{id}/roles", {
                    "user_id": user_id,
                    "role_id": role.get('value')
                })
            user['roles'] = user.get('roles', []) + new_roles
            changes.append(f"Added {len(new_roles)} role(s)")
            
        elif op == 'remove' and 'roles' in str(operation):
            old_roles = user.get('roles', [])
            for role in old_roles:
                simulate_cloud_app_call("DELETE /api/users/{id}/roles/{role_id}", {
                    "user_id": user_id,
                    "role_id": role.get('value')
                })
            user['roles'] = []
            changes.append("Removed all roles")
            
        elif op == 'replace':
            if 'active' in value:
                user['active'] = value['active']
                simulate_cloud_app_call("PATCH /api/users/{id}", {
                    "user_id": user_id,
                    "active": value['active']
                })
                changes.append(f"User {'activated' if value['active'] else 'deactivated'}")
            
            if 'roles' in value:
                user['roles'] = value['roles']
                changes.append("Replaced all roles")
    
    user['modified'] = datetime.utcnow().isoformat() + "Z"
    log_activity("User Updated", f"Updated user {user['userName']}: {'; '.join(changes)}")
    
    print(f"   ✅ User patched successfully")
    print(f"{'='*70}\n")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user.get("roles", []),
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["modified"]
        }
    })

@app.route('/scim/v2/Users', methods=['GET'])
def list_users():
    """List/search users"""
    
    filter_param = request.args.get('filter', '')
    start_index = int(request.args.get('startIndex', 1))
    count = int(request.args.get('count', 100))
    
    users = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": user["id"],
            "userName": user["userName"],
            "name": user["name"],
            "emails": user["emails"],
            "active": user["active"],
            "roles": user.get("roles", []),
            "meta": {
                "resourceType": "User",
                "created": user["created"],
                "lastModified": user.get("modified", user["created"])
            }
        }
        for user in users_db.values()
    ]
    
    if filter_param and 'userName eq' in filter_param:
        match = re.search(r'userName eq "([^"]+)"', filter_param)
        if match:
            target_username = match.group(1)
            users = [u for u in users if u['userName'] == target_username]
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(users),
        "startIndex": start_index,
        "itemsPerPage": min(count, len(users)),
        "Resources": users[start_index-1:start_index-1+count]
    })

@app.route('/scim/v2/Users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    
    if user_id in users_db:
        username = users_db[user_id]['userName']
        simulate_cloud_app_call("DELETE /api/users/{id}", {"user_id": user_id})
        del users_db[user_id]
        log_activity("User Deleted", f"Deleted user {username}")
        return '', 204
    else:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "SCIM Entitlements Demo",
        "repository": "joevanhorn/api-entitlements-demo",
        "users": len(users_db),
        "active_users": sum(1 for u in users_db.values() if u.get('active', True)),
        "roles": len(entitlements_db),
        "activities": len(activity_log),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

if __name__ == '__main__':
    auth_token = os.environ.get('SCIM_AUTH_TOKEN', 'demo-token-12345')
    app.config['SCIM_AUTH_TOKEN'] = auth_token
    
    print("\n" + "="*70)
    print(" "*15 + "🚀 SCIM ENTITLEMENTS DEMO SERVER")
    print("="*70)
    print(f"📦 Repository: joevanhorn/api-entitlements-demo")
    print(f"📍 Dashboard: http://localhost:5000")
    print(f"📍 SCIM API: http://localhost:5000/scim/v2")
    print(f"🔑 Auth Token: Bearer {auth_token}")
    print(f"🎭 Available Roles: {len(entitlements_db)}")
    for role in entitlements_db.values():
        print(f"   • {role['name']} - {role['description']}")
    print("="*70)
    print("\n⏳ Starting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
