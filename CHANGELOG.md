# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-15

### Added

- Initial release of rackfish
- Dynamic Redfish client with lazy loading
- Automatic OEM and Links property surfacing
- Action method binding with ActionInfo validation
- Collection iteration support
- Session and basic authentication
- Support for 150+ common Redfish operations
- Comprehensive documentation and examples
- Full test suite with 100% passing tests
- Support for Huawei, Dell, HPE, Lenovo, Supermicro and all Redfish-compliant BMCs

### Features

- Zero external dependencies (except `requests`)
- Lazy resource fetching for performance
- Dynamic attribute mapping from JSON
- Collision-safe OEM/Links surfacing
- Type-safe action parameter validation
- Pythonic API with natural dot notation
- Thread-safe HTTP session management
- Recursion guard for deeply nested structures

### Documentation

- Complete API documentation
- 150+ usage examples
- Use case index
- Test suite documentation
- Comprehensive README
- GitHub/PyPI ready structure

[1.0.0]: https://github.com/yourusername/rackfish/releases/tag/v1.0.0
