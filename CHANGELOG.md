# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed

- Prepared the project for a public GitHub repository.
- Reworked the README and installation guidance for repository-based distribution.
- Replaced internal delivery provenance metadata with public project documentation.
- Added English User Guide and Safety Instructions while retaining the Chinese editions.
- Made first-use initialization explicitly state that both `xxx` and `yyy` must each be unique for every new Mem on the same Mac.

### Removed

- Removed bundled regression tests, generated validation results and delivery reports.

## [9.9.9] - 2026-09-13

### Added

- Native macOS launchers and runtime checks.
- CDP/DOM browser control with profile ownership verification and safe tab lifecycle.
- Screenshot, mouse, keyboard, bounded wait and external Mem components.
- User- and project-scoped Skill installation with external runtime data.

### Security

- Restricted CDP to loopback endpoints and Mem-bound browser profiles.
- Kept authentication secrets, browser profiles and active memory out of the package.
