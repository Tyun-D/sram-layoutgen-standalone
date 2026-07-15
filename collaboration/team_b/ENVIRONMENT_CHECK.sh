#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
project_branch_expected="collab/team-b-control-support"
project_head="$(git -C "$repo_root" rev-parse HEAD)"
project_branch="$(git -C "$repo_root" branch --show-current)"
openyield_head="$(git -C /data1/qujh/work/external/OpenYield rev-parse HEAD)"

echo "project_branch=$project_branch"
echo "project_head=$project_head"
echo "openyield_head=$openyield_head"

if [[ "$project_branch" != "$project_branch_expected" ]]; then
  echo "ERROR: expected branch $project_branch_expected" >&2
  exit 1
fi

if [[ "$openyield_head" != "1c34428d8b913963c4971d093b1a7c2df97a2509" ]]; then
  echo "ERROR: OpenYield HEAD mismatch" >&2
  exit 1
fi

for tool in git rg sha256sum tar; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "ERROR: missing required tool $tool" >&2
    exit 1
  }
done

for cell in \
  outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds \
  outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW250_PW500_L50/PINV_NW250_PW500_L50.gds \
  outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50.gds \
  collaboration/team_b/START_HERE.md; do
  [[ -e "$repo_root/$cell" ]] || {
    echo "ERROR: required path missing: $cell" >&2
    exit 1
  }
done

echo "allowed_path_writability_check=report_only"
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  parent="$repo_root/${path%/*}"
  if [[ -d "$parent" ]]; then
    [[ -w "$parent" ]] && echo "allowed_parent_writable=$path" || echo "allowed_parent_not_writable=$path"
  else
    echo "allowed_parent_missing=$path"
  fi
done < "$repo_root/collaboration/ALLOWED_PATHS_TEAM_B.txt"

echo "forbidden_path_clean_check=working_tree_only"
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if git -C "$repo_root" diff --quiet -- "$path"; then
    echo "forbidden_clean=$path"
  else
    echo "ERROR: forbidden path modified: $path" >&2
    exit 1
  fi
done < "$repo_root/collaboration/FORBIDDEN_PATHS_TEAM_B.txt"

echo "environment_check=PASS"
