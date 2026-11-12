# Contributing

Thanks for your interest in contributing to **acer-alg-kbd-rgb**!

## Reporting Issues

If you encounter a bug or have a feature request, please [open an issue](../../issues) with:

1. Your **distro** and **kernel version** (`uname -r`)
2. Output of `alg-kbd-rgb --status`
3. Output of `dkms status`
4. Steps to reproduce the problem

## Pull Requests

1. Fork the repo and create a branch from `main`.
2. If you changed kernel driver sources, explain what was modified and why.
3. Test your changes on at least one supported distro.
4. Open a PR with a clear description.

## Kernel Driver Changes

The files under `driver-src/` are derived from [tuxedo-drivers v4.25.1](https://github.com/tuxedocomputers/tuxedo-drivers). If you need to patch them:
- Keep the SPDX and copyright headers intact.
- Document your changes clearly in the commit message.
- Consider contributing fixes upstream to the tuxedo-drivers project as well.

## Code Style

- **Shell scripts:** Follow `shellcheck` recommendations.
- **Python:** PEP 8, type hints where practical.
- **C (kernel):** Follow Linux kernel coding style.

## License

By contributing, you agree that your contributions will be licensed under **GPL-2.0-or-later**.
