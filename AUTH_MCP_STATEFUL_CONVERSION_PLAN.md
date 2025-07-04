# Auth MCP Server: Stateless to Stateful Conversion Plan

> **Objective**: Convert the TypeScript auth MCP server from stateless to stateful to serve as a proper template for MC-PEA generation

## 🎯 **Current State vs Target State**

### **Current (Stateless)**:
```
Client Request → Auth Server → Immediate Response
No session storage, no state persistence
```

### **Target (Stateful)**:
```
Client Request → Session Check → Auth Server → Session Update → Response
Session storage, state persistence, connection lifecycle
```

## 🔧 **Required Changes**

### 1. **Session Management Infrastructure**

Add session management layer:

```typescript
// src/session/SessionManager.ts
export interface Session {
  id: string;
  clientInfo: {
    name: string;
    version: string;
  };
  createdAt: Date;
  lastActivity: Date;
  authenticated: boolean;
  userId?: string;
  permissions: string[];
}

export class SessionManager {
  private sessions = new Map<string, Session>();
  
  createSession(clientInfo: any): string {
    const sessionId = crypto.randomUUID();
    const session: Session = {
      id: sessionId,
      clientInfo,
      createdAt: new Date(),
      lastActivity: new Date(),
      authenticated: false,
      permissions: []
    };
    
    this.sessions.set(sessionId, session);
    return sessionId;
  }
  
  getSession(sessionId: string): Session | null {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.lastActivity = new Date();
      return session;
    }
    return null;
  }
  
  updateSession(sessionId: string, updates: Partial<Session>): boolean {
    const session = this.sessions.get(sessionId);
    if (session) {
      Object.assign(session, updates);
      session.lastActivity = new Date();
      return true;
    }
    return false;
  }
  
  destroySession(sessionId: string): boolean {
    return this.sessions.delete(sessionId);
  }
  
  cleanupExpiredSessions(maxAge: number = 30 * 60 * 1000): void {
    const now = new Date();
    for (const [sessionId, session] of this.sessions) {
      if (now.getTime() - session.lastActivity.getTime() > maxAge) {
        this.sessions.delete(sessionId);
      }
    }
  }
}
```

### 2. **Session-Aware Request Handler**

Update the main server to handle sessions:

```typescript
// src/index.ts (main changes)
import { SessionManager } from './session/SessionManager.js';

export class StatefulAuthMCPServer {
  private sessionManager = new SessionManager();
  
  async handleRequest(request: any): Promise<any> {
    // Extract session ID from headers or request
    const sessionId = this.extractSessionId(request);
    
    // Handle session establishment
    if (request.method === 'session/start') {
      return this.handleSessionStart(request);
    }
    
    // Validate session for other requests
    if (!sessionId || !this.sessionManager.getSession(sessionId)) {
      return this.createErrorResponse(request.id, -32600, 'Bad Request: Missing or invalid session ID');
    }
    
    // Process request with session context
    return this.processWithSession(request, sessionId);
  }
  
  private handleSessionStart(request: any) {
    const sessionId = this.sessionManager.createSession(request.params?.clientInfo);
    
    return {
      jsonrpc: '2.0',
      id: request.id,
      result: {
        sessionId,
        message: 'Session established successfully',
        capabilities: this.getServerCapabilities()
      }
    };
  }
  
  private extractSessionId(request: any): string | null {
    // Check headers first (HTTP transport)
    if (request.headers?.['x-session-id']) {
      return request.headers['x-session-id'];
    }
    
    // Check request params (WebSocket/stdio transport)
    if (request.params?.sessionId) {
      return request.params.sessionId;
    }
    
    return null;
  }
  
  private async processWithSession(request: any, sessionId: string) {
    const session = this.sessionManager.getSession(sessionId);
    
    switch (request.method) {
      case 'initialize':
        return this.handleInitialize(request, session);
      case 'auth/login':
        return this.handleLogin(request, session);
      case 'auth/logout':
        return this.handleLogout(request, session);
      case 'auth/validate':
        return this.handleValidate(request, session);
      case 'tools/list':
        return this.handleToolsList(request, session);
      case 'tools/call':
        return this.handleToolCall(request, session);
      default:
        return this.createErrorResponse(request.id, -32601, 'Method not found');
    }
  }
}
```

### 3. **Session-Aware Authentication Tools**

Update authentication tools to use session state:

```typescript
// src/tools/auth-tools.ts
export class SessionAwareAuthTools {
  constructor(private sessionManager: SessionManager) {}
  
  async login(params: any, sessionId: string) {
    const { username, password } = params;
    
    // Validate credentials (implement your auth logic)
    const user = await this.validateCredentials(username, password);
    
    if (user) {
      // Update session with authenticated user
      this.sessionManager.updateSession(sessionId, {
        authenticated: true,
        userId: user.id,
        permissions: user.permissions
      });
      
      return {
        success: true,
        user: {
          id: user.id,
          username: user.username,
          permissions: user.permissions
        },
        sessionId // Return session ID for client reference
      };
    } else {
      return {
        success: false,
        error: 'Invalid credentials'
      };
    }
  }
  
  async validate(params: any, sessionId: string) {
    const session = this.sessionManager.getSession(sessionId);
    
    if (!session || !session.authenticated) {
      return {
        valid: false,
        error: 'Not authenticated'
      };
    }
    
    return {
      valid: true,
      user: {
        id: session.userId,
        permissions: session.permissions
      },
      sessionInfo: {
        createdAt: session.createdAt,
        lastActivity: session.lastActivity
      }
    };
  }
  
  async logout(params: any, sessionId: string) {
    this.sessionManager.updateSession(sessionId, {
      authenticated: false,
      userId: undefined,
      permissions: []
    });
    
    return {
      success: true,
      message: 'Logged out successfully'
    };
  }
}
```

### 4. **Session Lifecycle Management**

Add session cleanup and management:

```typescript
// src/session/SessionLifecycle.ts
export class SessionLifecycle {
  private cleanupInterval: NodeJS.Timeout;
  
  constructor(private sessionManager: SessionManager) {
    // Cleanup expired sessions every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.sessionManager.cleanupExpiredSessions();
    }, 5 * 60 * 1000);
  }
  
  async handleServerShutdown() {
    clearInterval(this.cleanupInterval);
    // Optionally persist sessions to storage
  }
  
  getSessionStats() {
    return {
      activeSessions: this.sessionManager.getActiveSessionCount(),
      totalSessions: this.sessionManager.getTotalSessionCount()
    };
  }
}
```

## 🔄 **Migration Steps**

### **Step 1: Add Session Management**
1. Create `SessionManager` class
2. Add session storage (in-memory initially)
3. Implement session CRUD operations

### **Step 2: Update Request Handling**
1. Add session ID extraction logic
2. Implement session validation middleware
3. Add session establishment endpoint

### **Step 3: Convert Tools to Session-Aware**
1. Update each auth tool to accept session context
2. Store authentication state in sessions
3. Implement session-based permissions

### **Step 4: Add Session Lifecycle**
1. Implement session cleanup
2. Add session monitoring
3. Handle graceful shutdown

### **Step 5: Update Protocol Responses**
1. Include session IDs in responses
2. Add session-related error codes
3. Update tool schemas

## 🧪 **Testing the Stateful Version**

Once converted, the server should require:

```javascript
// 1. Start session
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "session/start",
  "params": {
    "clientInfo": { "name": "test-client", "version": "1.0.0" }
  }
}

// 2. Use session ID in subsequent requests
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "auth/login",
  "params": {
    "sessionId": "session-uuid-here",
    "username": "testuser",
    "password": "testpass"
  }
}
```

## 📝 **File Structure After Conversion**

```
auth-mcp-server/
├── src/
│   ├── session/
│   │   ├── SessionManager.ts
│   │   └── SessionLifecycle.ts
│   ├── tools/
│   │   ├── auth-tools.ts (updated)
│   │   └── session-tools.ts (new)
│   ├── types/
│   │   ├── session.ts
│   │   └── auth.ts
│   └── index.ts (updated)
├── package.json
└── README.md (updated)
```

## 🎯 **Benefits as MC-PEA Template**

This stateful version becomes a perfect template because:
1. **Session Management**: Shows how to handle state in MCP servers
2. **TypeScript Implementation**: Aligns with MCP protocol best practices
3. **Scalable Architecture**: Demonstrates proper separation of concerns
4. **Production Ready**: Includes lifecycle management and cleanup

Would you like me to help implement any specific part of this conversion?
