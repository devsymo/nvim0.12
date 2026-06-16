#!/usr/bin/env bash
# build-neovim-rpm.sh
# ---------------------------------------------------------------------------
# Sets up an rpmbuild workspace and builds the neovim RPM from neovim.spec.
# Run as a non-root user with sudo access for dependency installation.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_FILE="${SCRIPT_DIR}/neovim.spec"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

[ -f "$SPEC_FILE" ] || error "neovim.spec not found at ${SPEC_FILE}"
command -v rpmbuild >/dev/null 2>&1 || error "rpmbuild not found — install rpm-build first."
command -v curl     >/dev/null 2>&1 || error "curl not found."

# Install build dependencies
info "Ensuring build dependencies are present..."
if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y rpm-build curl tar gzip
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y rpm-build curl tar gzip
else
    warn "Neither dnf nor yum found — ensure rpm-build, curl, tar, gzip are installed."
fi

# Set up rpmbuild tree
RPMBUILD_ROOT="${HOME}/rpmbuild"
info "Setting up rpmbuild tree at ${RPMBUILD_ROOT}..."
mkdir -p "${RPMBUILD_ROOT}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
cp "$SPEC_FILE" "${RPMBUILD_ROOT}/SPECS/neovim.spec"

# Build
info "Starting rpmbuild (neovim + tree-sitter-cli will be downloaded during build)..."
rpmbuild -ba \
    --define "_topdir ${RPMBUILD_ROOT}" \
    "${RPMBUILD_ROOT}/SPECS/neovim.spec"

# Results
echo ""
info "Build complete. RPM(s) produced:"
find "${RPMBUILD_ROOT}/RPMS" -name "neovim*.rpm" | while read -r rpm; do
    echo "  ${rpm}"
done
echo ""
info "To install:"
echo "  sudo rpm -ivh \$(find ${RPMBUILD_ROOT}/RPMS -name 'neovim*.rpm' | head -1)"
echo "  # or with dnf:"
echo "  sudo dnf install \$(find ${RPMBUILD_ROOT}/RPMS -name 'neovim*.rpm' | head -1)"
