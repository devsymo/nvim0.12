Name:           neovim
Version:        0.12.3
Release:        1%{?dist}
Summary:        Vim-fork focused on extensibility and usability
License:        Apache-2.0 AND Vim
URL:            https://neovim.io

# No BuildRequires for compilers — both artefacts are pre-built binaries.
BuildRequires:  curl
BuildRequires:  tar
BuildRequires:  gzip

%description
Neovim is a project that seeks to aggressively refactor Vim in order to:
  * Simplify maintenance and encourage contributions
  * Split the work between multiple developers
  * Enable advanced UIs without modifications to the core
  * Maximize extensibility

Installation layout
  /usr/local/nvim-0.12.3/          — unpacked release tarball
  /usr/local/bin/nvim              — symlink → ../nvim-0.12.3/bin/nvim

tree-sitter-cli (v0.26.9) is bundled and installed to /usr/local/bin/tree-sitter
only when no existing tree-sitter-cli with version > 0.26.1 is found on the system.

# ============================================================
%prep
# ============================================================

# ---- Neovim ----
echo "Downloading neovim v%{version}..."
curl -fSLO "https://github.com/neovim/neovim/releases/download/v%{version}/nvim-linux-x86_64.tar.gz"
# Unpack into a staging dir; keep the top-level directory name intact
# so that after install it lands at /usr/local/nvim-0.12.3
tar -xvf nvim-linux-x86_64.tar.gz
# The tarball extracts to nvim-linux-x86_64/
mv nvim-linux-x86_64 nvim-%{version}

# ---- tree-sitter-cli ----
echo "Downloading tree-sitter-cli v0.26.9..."
curl -fSLO "https://github.com/tree-sitter/tree-sitter/releases/download/v0.26.9/tree-sitter-linux-x64.gz"
gunzip -f tree-sitter-linux-x64.gz
chmod +x tree-sitter-linux-x64

# ============================================================
%build
# ============================================================
# Pre-compiled binaries — nothing to build.

# ============================================================
%install
# ============================================================
rm -rf %{buildroot}

# ---------- Neovim: install the full unpacked tree ----------
# Mirrors:  sudo mv nvim-linux-x86_64 /usr/local/nvim-0.12.3
install -d %{buildroot}/usr/local/nvim-%{version}
cp -a %{_builddir}/nvim-%{version}/. \
      %{buildroot}/usr/local/nvim-%{version}/

# ---------- Neovim: symlink ----------
# Mirrors:  sudo ln -s /usr/local/nvim-0.12.3/bin/nvim /usr/local/bin/nvim
install -d %{buildroot}/usr/local/bin
ln -s /usr/local/nvim-%{version}/bin/nvim \
      %{buildroot}/usr/local/bin/nvim

# ---------- tree-sitter-cli: stage the binary ----------
# The actual placement into /usr/local/bin is deferred to %post so we
# can inspect the system's existing tree-sitter version at install time.
# We store it under /usr/local/lib/neovim/ which RPM will track.
install -d %{buildroot}/usr/local/lib/neovim
install -m 0755 %{_builddir}/tree-sitter-linux-x64 \
                %{buildroot}/usr/local/lib/neovim/tree-sitter

# ============================================================
%pre
# ============================================================
# Determine at install time whether the bundled tree-sitter-cli is needed.
#
# Condition: skip if an existing `tree-sitter` binary reports a version
#            strictly greater than 0.26.1.
#
# The result is recorded via a flag file because RPM scriptlets (%pre, %post)
# are separate shell invocations and cannot share variables.

_ts_ver_gt_0261() {
    # Returns 0 (true) when the version string $1 is > 0.26.1
    local IFS=.
    # shellcheck disable=SC2086
    set -- $1
    local major="${1:-0}" minor="${2:-0}" patch="${3:-0}"
    if   [ "$major" -gt 0 ]; then return 0
    elif [ "$major" -lt 0 ]; then return 1; fi
    if   [ "$minor" -gt 26 ]; then return 0
    elif [ "$minor" -lt 26 ]; then return 1; fi
    [ "$patch" -gt 1 ]
}

NEEDS_TS=1

if command -v tree-sitter >/dev/null 2>&1; then
    EXISTING_VER=$(tree-sitter --version 2>/dev/null \
                   | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$EXISTING_VER" ] && _ts_ver_gt_0261 "$EXISTING_VER"; then
        echo "neovim rpm: tree-sitter-cli ${EXISTING_VER} > 0.26.1 found — skipping bundled install."
        NEEDS_TS=0
    else
        echo "neovim rpm: tree-sitter-cli ${EXISTING_VER:-not found} does not satisfy > 0.26.1 — bundled v0.26.9 will be installed."
    fi
fi

if [ "$NEEDS_TS" -eq 1 ]; then
    touch /tmp/.neovim_needs_ts 2>/dev/null || true
else
    rm -f /tmp/.neovim_needs_ts 2>/dev/null || true
fi

# ============================================================
%post
# ============================================================
# Mirrors:  sudo ln -s ... /usr/local/bin/tree-sitter  (or cp for a real binary)
if [ -f /tmp/.neovim_needs_ts ]; then
    echo "neovim rpm: installing tree-sitter-cli v0.26.9 → /usr/local/bin/tree-sitter"
    install -m 0755 /usr/local/lib/neovim/tree-sitter /usr/local/bin/tree-sitter
    rm -f /tmp/.neovim_needs_ts
fi

# ============================================================
%preun
# ============================================================
# On full uninstall ($1 == 0): remove the symlink and, if we placed the
# tree-sitter binary, remove that too.
if [ "$1" -eq 0 ]; then
    # Remove nvim symlink
    rm -f /usr/local/bin/nvim

    # Remove tree-sitter only if it is the copy we installed
    if cmp -s /usr/local/bin/tree-sitter \
              /usr/local/lib/neovim/tree-sitter 2>/dev/null; then
        echo "neovim rpm: removing /usr/local/bin/tree-sitter"
        rm -f /usr/local/bin/tree-sitter
    fi
fi

# ============================================================
%files
# ============================================================
# The full nvim install tree
/usr/local/nvim-%{version}/

# The nvim symlink
/usr/local/bin/nvim

# The staged tree-sitter binary (always owned by this package)
/usr/local/lib/neovim/tree-sitter

# NOTE: /usr/local/bin/tree-sitter is NOT listed here because it is
# created conditionally in %post (RPM cannot own ghost symlinks that
# may not exist). %preun cleans it up on uninstall.

# ============================================================
%changelog
# ============================================================
* Tue Jun 16 2026 Package Maintainer <maintainer@example.com> - 0.12.3-1
- Initial package for Neovim 0.12.3
- Installs to /usr/local/nvim-0.12.3 with symlink at /usr/local/bin/nvim
- Bundles tree-sitter-cli v0.26.9; installed only when system version <= 0.26.1
