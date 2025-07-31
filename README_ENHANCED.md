# Enhanced Metasploit Framework MCP Server

A comprehensive, production-ready MCP (Model Context Protocol) server for Metasploit Framework integration with advanced features, security, and performance optimizations.

## 🚀 Features

### Core Capabilities
- **Dual-Mode Operation**: Seamless switching between RPC and Resource Script modes
- **Advanced Security**: Comprehensive validation, threat detection, and audit logging
- **High Performance**: Caching, connection pooling, and result streaming
- **Real-time Operations**: Direct database access, session management, and module operations
- **Flexible Configuration**: Environment-specific settings with runtime updates

### Enhanced Tools
1. **Database Operations**: Advanced querying with parsed results
2. **Session Management**: Real-time session interaction and monitoring
3. **Module Operations**: Live module configuration and execution
4. **Workspace Management**: Complete workspace lifecycle support
5. **Payload Generation**: Comprehensive msfvenom integration
6. **Security Monitoring**: Threat detection and audit trails
7. **Performance Analytics**: Real-time metrics and optimization

## 📋 Prerequisites

- **Python 3.8+**
- **Metasploit Framework** (latest version recommended)
- **MCP SDK** (automatically installed)
- **System privileges** (for certain operations)

## 🛠️ Installation

### Quick Start
```bash
# Clone or navigate to the directory
cd /path/to/msfconsole

# Run the enhanced setup
./start_enhanced_mcp.sh setup

# Start the server
./start_enhanced_mcp.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv_enhanced
source venv_enhanced/bin/activate

# Install dependencies
pip install -r requirements_enhanced.txt

# Initialize configuration
python3 -c "from msf_config import ConfigurationManager; ConfigurationManager().create_default_config_file()"

# Start server
python3 msfconsole_mcp_enhanced.py
```

## ⚙️ Configuration

### Configuration File (`msf_mcp_config.yaml`)
```yaml
environment: development  # development, testing, production

rpc:
  host: "127.0.0.1"
  port: 55552
  username: "msf"
  password: "msf123"
  ssl: false
  timeout: 30

security:
  max_command_length: 1000
  command_timeout: 120
  enable_audit_logging: true
  require_workspace_isolation: true

performance:
  cache_enabled: true
  cache_ttl: 300
  max_batch_size: 50
  connection_pooling: true

logging:
  level: "INFO"
  file_path: "msfconsole_mcp_enhanced.log"
```

### Environment Variables
```bash
export MSF_MCP_ENVIRONMENT="production"
export MSF_RPC_HOST="127.0.0.1"
export MSF_RPC_PORT="55552"
export MSF_SECURITY_AUDIT_LOGGING="true"
export MSF_PERFORMANCE_CACHE_ENABLED="true"
```

## 🔧 Available Tools

### Core Operations
- `get_msf_status` - Get comprehensive system status
- `execute_msf_command` - Execute any MSF command with security validation
- `search_modules` - Advanced module search with filtering
- `manage_workspaces` - Complete workspace management

### Database Operations
- `database_operations` - Query hosts, services, vulnerabilities, credentials
- Advanced parsing and structured results
- Filter support for targeted queries

### Session Management
- `session_management` - List, interact, execute commands in sessions
- Real-time session monitoring
- Security validation for session commands

### Module Operations
- `module_operations` - Load, configure, and execute modules
- Batch option setting
- Payload compatibility checking

### Payload Generation
- `payload_generation` - Advanced msfvenom integration
- Security validation for payload options
- Multiple output formats

### Resource Scripts
- `resource_script_execution` - Batch command execution
- Automated script generation
- Performance optimization for large scripts

## 🔒 Security Features

### Command Validation
- **Syntax Checking**: Validates command structure
- **Keyword Blocking**: Prevents dangerous system commands
- **Module Validation**: Ensures only authorized modules
- **Input Sanitization**: Removes malicious characters

### Threat Detection
- **Pattern Analysis**: Detects known attack patterns
- **Risk Scoring**: Assigns risk levels to operations
- **Audit Logging**: Comprehensive security event logging
- **Session Monitoring**: Tracks session activities

### Access Control
- **Workspace Isolation**: Enforces workspace boundaries
- **Session Limits**: Prevents resource exhaustion
- **Timeout Management**: Prevents long-running operations

## ⚡ Performance Optimizations

### Caching System
- **LRU Cache**: Intelligent cache management
- **TTL Support**: Time-based cache expiration
- **Memory Limits**: Prevents memory exhaustion
- **Hit Rate Monitoring**: Performance analytics

### Connection Management
- **Connection Pooling**: Reuses RPC connections
- **Health Checking**: Monitors connection status
- **Auto-Reconnection**: Handles connection failures
- **Load Balancing**: Distributes requests efficiently

### Result Streaming
- **Chunked Responses**: Handles large outputs
- **Memory Optimization**: Prevents memory spikes
- **Progress Tracking**: Real-time operation status

## 📊 Monitoring & Analytics

### Performance Metrics
```bash
# Get real-time metrics
curl -X POST http://localhost:8080/metrics

# Metrics include:
# - Request/response times
# - Cache hit rates
# - Memory usage
# - Connection status
# - Error rates
```

### Security Analytics
- **Threat Level Tracking**: Monitor security events
- **Command Analysis**: Track command patterns
- **User Behavior**: Detect anomalous activities
- **Compliance Reporting**: Generate security reports

## 🚦 Usage Examples

### Basic Command Execution
```python
# Execute a simple command
result = await execute_msf_command(
    command="hosts",
    workspace="pentest_2024"
)
```

### Advanced Module Operation
```python
# Configure and execute a module
result = await module_operations(
    action="execute",
    module_path="auxiliary/scanner/portscan/tcp",
    options={
        "RHOSTS": "192.168.1.0/24",
        "PORTS": "1-1000",
        "THREADS": "50"
    }
)
```

### Batch Operations
```python
# Execute multiple commands
commands = [
    "use auxiliary/scanner/discovery/arp_sweep",
    "set RHOSTS 192.168.1.0/24",
    "run",
    "hosts"
]

result = await resource_script_execution(
    script_commands=commands,
    workspace="network_scan"
)
```

## 🐛 Troubleshooting

### Common Issues

1. **RPC Connection Failed**
   ```bash
   # Check if msfrpcd is running
   ps aux | grep msfrpcd
   
   # Start msfrpcd manually
   msfrpcd -U msf -P msf123 -f
   ```

2. **Permission Denied**
   ```bash
   # Ensure proper permissions
   sudo chown -R $(whoami):$(whoami) /path/to/msfconsole
   ```

3. **Database Not Connected**
   ```bash
   # Initialize Metasploit database
   sudo msfdb init
   sudo msfdb start
   ```

### Debug Mode
```bash
# Enable debug logging
export MSF_LOG_LEVEL="DEBUG"
python3 msfconsole_mcp_enhanced.py
```

### Health Check
```bash
# Run system health check
./start_enhanced_mcp.sh check
```

## 📈 Performance Tuning

### High-Load Environments
```yaml
performance:
  cache_enabled: true
  cache_max_size: 5000
  connection_pool_size: 20
  max_batch_size: 100
  async_operations: true
```

### Memory-Constrained Systems
```yaml
performance:
  cache_enabled: false
  connection_pool_size: 3
  max_batch_size: 10
  memory_limit_mb: 256
```

## 🔄 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  Enhanced MCP   │
│                 │    │     Server      │
└─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼──┐ ┌──────▼──┐ ┌─────▼─────┐
            │   RPC    │ │Resource │ │ Security  │
            │ Manager  │ │Scripts  │ │ Manager   │
            └───────┬──┘ └──────┬──┘ └─────┬─────┘
                    │           │          │
            ┌───────▼───────────▼──────────▼─────┐
            │        Dual-Mode Handler           │
            └────────────────┬───────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │   Metasploit      │
                   │   Framework       │
                   └───────────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Ensure security validation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is designed for authorized security testing only. Always ensure you have proper permission before testing any systems. The authors are not responsible for misuse of this software.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via GitHub issues
- **Security**: Report security issues privately to maintainers
- **Community**: Join discussions in project forums

---

**Enhanced MSF MCP Server v2.0.0** - Production-ready Metasploit integration with enterprise-grade features.