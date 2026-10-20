# Source objects

Each `.py` filename is the SHA-256 of its exact contents. The experiment profile
index in `results/sp2027-source-map/index.json` maps recorded source paths to
these objects. Objects include sources recovered from repository history and
intermediate revisions verified against contemporaneous manifest hashes.

`scripts/capture_source_snapshots.py` checks and extends this collection.
`scripts/materialize_profile.py` reconstructs a named experiment's source tree
without overwriting the current implementation. Current tests apply to the
current implementation; frozen profiles preserve earlier experiment entry
points and dependencies for reproduction.
Profiles also list required data inputs. Materialization verifies and stages
those files, so historical probes and targeted diagnostics can resolve their
recorded inputs inside the reconstructed tree.
