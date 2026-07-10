# Hacking: MySQL Snap Build Internals

This document records build-internals that are correct but non-obvious,
so future maintainers don't "fix" things that are already right.

## Install Layout: DEB (usr/bin/, usr/sbin/)

MySQL is built with `-DINSTALL_LAYOUT=DEB` and
`-DCMAKE_INSTALL_PREFIX=/usr`. This puts client CLIs in `usr/bin/`,
the server (`mysqld`) in `usr/sbin/`, plugins in
`usr/lib/mysql/plugin/`, and shared data in
`usr/share/mysql/` — all under the snap root.

This matches the previous 8.4 snap (which repackaged the
`mysql-server` deb) and the Debian packaging conventions.

1. **It matches MySQL's compiled-in DEB defaults** — the DEB layout
   sets `secure_file_priv` to `/var/lib/mysql-files` (overridden to
   `NULL` in `my.cnf`) and the compiled-in plugin directory to
   `/usr/lib/mysql/plugin`. Since the binary lives at
   `$SNAP/usr/sbin/mysqld`, MySQL auto-detects its basedir as
   `$SNAP/usr` (by stripping `/sbin/mysqld` from its own path), so
   plugin loading and shared-data resolution work without any
   `--basedir` flag. No `plugin-dir` or `lc-messages-dir` override is
   needed in `my.cnf`.

2. **It coexists with the `packages-deb` part** — `util-linux`
   (which provides `setpriv`) also installs to `usr/bin/setpriv`. The
   MySQL client CLIs land in `usr/bin/` alongside it; the server
   (`mysqld`) is in `usr/sbin/`, avoiding any collision.

Consequence: the `apps:` block references `usr/bin/<cli>` for client
tools, `mysqld.sh` and the install hook reference
`$SNAP/usr/sbin/mysqld` with no `--basedir` flag. `my.cnf` does NOT
set `plugin-dir` or `lc-messages-dir` — MySQL auto-detects basedir from
its binary path. Do not add `--basedir`, `plugin-dir`, or
`lc-messages-dir` back.

## Runtime Library Provenance

The source-built MySQL binaries depend on shared libraries provided by
two sources: the `core26` base snap and stage-packages inside the snap.

### Base-provided libraries (core26, NOT staged)

These are provided by the `core26` base snap at
`/snap/core26/current/usr/lib/x86_64-linux-gnu/` and must NOT be
duplicated in `stage-packages`:

| .so name      | core26 package |
|---------------|----------------|
| libgcc_s.so.1 | libgcc-s1      |
| libstdc++.so.6| libstdc++6     |

Additional base-provided libs used transitively: libc.so.6, libm.so.6,
liblzma.so.5, libxxhash.so.0, libresolv.so.2, libtinfo.so.6,
libbsd.so.0, libmd.so.0.

### Staged libraries (stage-packages, inside the snap)

| .so name                  | stage-package              | Used by               |
|---------------------------|----------------------------|-----------------------|
| libicuuc.so.78            | libicu78                   | mysqld                |
| libicui18n.so.78          | libicu78                   | mysqld                |
| libicudata.so.78          | libicu78                   | mysqld                |
| libssl.so.3               | libssl3t64                 | mysqld, client CLIs   |
| libcrypto.so.3            | libssl3t64                 | mysqld, client CLIs   |
| libzstd.so.1              | libzstd1                   | mysqld, client CLIs   |
| libprotobuf-lite.so.32    | libprotobuf-lite32t64      | mysqld, group_replication |
| libprotobuf.so.32         | libprotobuf32t64           | component_telemetry, telemetry_client |
| libz.so.1                 | zlib1g                     | mysqld, client CLIs   |
| liblz4.so.1               | liblz4-1                   | mysqld                |
| libaio.so.1t64            | libaio1t64                 | mysqld                |
| libnuma.so.1              | libnuma1                   | mysqld                |
| libtcmalloc.so.4          | libgoogle-perftools4t64    | mysqld, client CLIs   |
| libunwind.so.8            | (transitive of libgoogle-perftools4t64) | mysqld, client CLIs |
| libedit.so.2              | libedit2                   | mysql CLI             |
| libcurl.so.4              | libcurl4t64                | component_telemetry, telemetry_client |
| libtirpc.so.3             | libtirpc3t64               | group_replication     |
| libmecab.so.2             | libmecab2                  | libpluginmecab        |

### Unused stage-packages (audit finding)

The following stage-packages are present but no binary or plugin links
their shared libraries. They are transitive dependencies or were added
for build-time availability. Removing them would shrink the snap but
re-triggers the full source build. Consider removing on the next
rebuild opportunity:

| stage-package          | .so in snap                 | Notes                          |
|------------------------|-----------------------------|--------------------------------|
| libfido2-1             | libfido2.so.1               | No FIDO component built in 9.7.1 |
| libevent-core-2.1-7t64 | libevent_core-2.1.so.7      | MySQL bundles its own libevent |
| libwrap0               | libwrap.so.0                | No binary links TCP wrappers   |

## CMake Install Prefix

`CMAKE_INSTALL_PREFIX=/usr` is correct. Do NOT change it to
`$CRAFT_PART_INSTALL`.

The snapcraft `cmake` plugin runs the install step with
`DESTDIR=$CRAFT_PART_INSTALL`. CMake's install logic produces
`${DESTDIR}${CMAKE_INSTALL_PREFIX}/...`, so:

- With prefix `/usr`: files land at `$CRAFT_PART_INSTALL/usr/bin/mysqld`,
  `$CRAFT_PART_INSTALL/usr/lib/mysql/plugin/...`, etc. — correct.
- With prefix `$CRAFT_PART_INSTALL`: files would land at
  `$CRAFT_PART_INSTALL/$CRAFT_PART_INSTALL/usr/bin/mysqld` — double-nested
  and broken.

No inline comment is added to `snapcraft.yaml` because any edit
(including comment-only) invalidates the craft-parts cache and
re-triggers the 30–60+ minute source compile. This document is the
comment.

## Base-bump Checklist

When the snap's `base:` changes (e.g. `core26` → `core28`):

1. **Re-resolve every `t64`/versioned `stage-package`**: Ubuntu
   version bumps rename packages (e.g. `libicu78` → `libicu80`,
   `libprotobuf-lite32t64` → `libprotobuf-liteXXt64`). Update every
   entry in the `mysql-server` part's `stage-packages`.

2. **Re-confirm `libgcc-s1`/`libstdc++6` are still in the new base**:
   These are NOT staged — the snap depends on the base snap providing
   them. Check with:
   ```
   ls /snap/<new-base>/current/usr/lib/x86_64-linux-gnu/libgcc_s.so.1
   ls /snap/<new-base>/current/usr/lib/x86_64-linux-gnu/libstdc++.so.6
   ```
   If the new base drops either, add it to `stage-packages`.

3. **Re-run the `ldd`/library-linter audit**: Unpack the rebuilt snap
   and run `ldd usr/sbin/mysqld` (and the client CLIs in
   `usr/bin/`) with
   `LD_LIBRARY_PATH=usr/lib/x86_64-linux-gnu`. Confirm every library
   resolves — either inside the snap or from the base. Run
   `snapcraft linters` and confirm no missing-library errors.

4. **Re-verify the `prime` glob safety**: List
   `usr/lib/mysql/plugin/` contents and confirm no production
   plugin matches `*test*` or `*example*`.
   A new MySQL minor version may add plugins whose names collide with
   the filter globs.

5. **Re-evaluate unused stage-packages**: The "Unused stage-packages"
   table above may change with a base bump — previously-unused packages
   may become needed, or new unused transitive deps may appear.
