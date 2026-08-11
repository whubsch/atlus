# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-10

### Added

- **Opening Hours Support**: New `get_hours()` function to parse raw opening hours strings into OSM `opening_hours` format
  - Support for multiple time formats and day abbreviations
  - Handles special OSM indicators like `PH` (public holiday)
  - Support for solar time keywords: `dawn`, `dusk`, `sunrise`, `sunset`
  - Comprehensive real-world test coverage
  
- **Point-in-Time Support**: New `get_times()` function to parse collection times, service times, and other point-in-time strings into OSM format
  - Gracefully handles closed days without erroring
  - Compatible with various time string formats

- **Output Validation**: New output validator to ensure parsed data conforms to OSM tagging standards

- **Expanded Language Support**: Expanded Spanish language coverage in abbreviation expansions

- **Enhanced Testing**: 
  - Real-world test cases from actual websites
  - Comprehensive test suite for opening hours and point-in-time parsing
  - Improved address tests

- **Build Tool Upgrade**: Migrated to `uv` package manager for faster dependency resolution and testing
  - Added `uv.lock` for reproducible builds
  - Updated tox configuration to use `uv`

- **Documentation**: 
  - Added opening_hours documentation
  - Updated README with new `get_hours()` and `get_times()` examples

### Changed

- Refactored core atlus module for better organization
- Improved error handling with clearer messages for unsupported calendar/date-based rules
- Enhanced address object structure for better data handling
- Updated GitHub Actions workflows for improved CI/CD

### Fixed

- Fixed merge conflicts from feature branch
- Corrected `Day.weekday_index` attribute naming in test suite
- Resolved issues with uv and tox integration

### Dependencies

- Updated GitHub Action versions for security and stability

[1.1.0]: https://github.com/whubsch/atlus/compare/1.0.1...1.1.0
