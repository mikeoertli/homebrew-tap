# Mike Oertli's Homebrew tap

Install and upgrade my various open source tools (mostly Go TUI utilities) with `brew`.
The tap builds pinned source archives, with prebuilt Homebrew bottles available
after the bottle publishing workflow has run for a release.

## Install

Once this repository's initial changes have been committed and pushed:

```sh
brew install mikeoertli/tap/krm
brew install mikeoertli/tap/gprm
brew install mikeoertli/tap/kcm
brew install mikeoertli/tap/shell-charm-progress
```

Homebrew adds the tap automatically. Alternatively:

```sh
brew tap mikeoertli/tap
brew install krm gprm kcm shell-charm-progress
```

| Package | Project documentation |
| --- | --- |
| `krm` | [kube-resource-monitor](https://github.com/mikeoertli/kube-resource-monitor#readme) |
| `gprm` | [github-pr-monitor](https://github.com/mikeoertli/github-pr-monitor#readme) |
| `kcm` | [kube-context-manager](https://github.com/mikeoertli/kube-context-manager#readme) |
| `shell-charm-progress` | [shell-charm-progress](https://github.com/mikeoertli/shell-charm-progress#readme) |

See each project's documentation for configuration, shell integration, and usage.
Homebrew installs the dependencies declared by its formula. Go is required only
when building from source; compatible bottles avoid local compilation.

If your Homebrew version asks you to trust a third-party formula, follow its
prompt, or use `brew trust --formula mikeoertli/tap/krm` on versions that support
that command. Trust additional packages individually as needed.

## Updates and removal

```sh
brew update
brew upgrade mikeoertli/tap/krm
brew upgrade                     # upgrade all outdated installed packages
brew uninstall mikeoertli/tap/krm
```

You can install the current upstream branch explicitly with
`brew install --HEAD mikeoertli/tap/krm`. HEAD is a development build; the default
installation always uses the pinned source in the formula.

For a reproducible collection in a `Brewfile`:

```ruby
tap "mikeoertli/tap"
brew "mikeoertli/tap/krm"
brew "mikeoertli/tap/gprm"
brew "mikeoertli/tap/kcm"
brew "mikeoertli/tap/shell-charm-progress"
```

Then run `brew bundle --file=Brewfile`.

## Maintainer workflow

`sources.json` records exact upstream commits, versions, archive hashes, and
whether a package is a snapshot. `templates/*.rb.in` contain the package build,
dependencies, tests, completions, and caveats. `scripts/update-formulas.py` updates
the source pins and checksums in `sources.json` and renders the corresponding
package definitions in `Formula/`, using Python 3's standard library.

Current package versions and pinned upstream commits are recorded in
[`sources.json`](sources.json). New tags are picked up by project dispatches or
the daily release-check workflow; ordinary branch pushes are not.

### Notify the tap when a project is tagged

A project's `homebrew.yml` workflow runs when a stable `vMAJOR.MINOR.PATCH` tag
is pushed. It dispatches this tap's `update.yml` workflow with the package name
and tag, so an update check starts immediately instead of waiting for the daily
schedule. The tap then opens an update PR and builds its bottles. Publishing
still uses the **brew pr-pull** step described below.

#### Set up the dispatch token

1. In your personal GitHub settings, go to **Developer settings → Personal access
   tokens → Fine-grained tokens → Generate new token**.
2. Set the resource owner to `mikeoertli`. Under **Repository access**, choose
   **Only select repositories** and select **homebrew-tap**. The token targets
   the tap, even though it will be stored in the projects sending notifications.
3. Under **Repository permissions**, grant **Actions: Read and write**. Generate
   the token and choose an expiration appropriate for your release schedule.
4. In each project repository, open **Settings → Secrets and variables → Actions →
   New repository secret**. Set its name to **TAP_DISPATCH_TOKEN** and its value
   to the token. Use a repository secret; the generated workflow does not select
   a GitHub Environment. The same tap-scoped token can be stored in each project.
5. Replace those secret values when the token expires or is rotated.

Using GitHub CLI, you can also add the secret interactively:

```sh
gh secret set TAP_DISPATCH_TOKEN --repo mikeoertli/my-tool
```

Enter the token at the prompt. The standard `GITHUB_TOKEN` in a project's
workflow is scoped to that project, so dispatching a workflow in the tap requires
this separate credential. See GitHub's [workflow dispatch permissions](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
and [repository secret setup](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-a-repository).

The tap also uses its own **TAP_UPDATE_TOKEN** to create update PRs. These are
separate roles:

| Repository secret | Store in | Access to `homebrew-tap` | Purpose |
| --- | --- | --- | --- |
| `TAP_DISPATCH_TOKEN` | Each project repository | Actions: Read and write | Trigger the tap's updater |
| `TAP_UPDATE_TOKEN` | Tap repository | Contents and Pull requests: Read and write | Push formula updates and open PRs |

#### Generate a workflow for a new project

The reusable template is [`templates/homebrew.yml.in`](templates/homebrew.yml.in).
Generate a project's workflow from this tap checkout:

```sh
python3 scripts/generate-workflow.py my-tool ~/develop/go/my-tool
```

The first argument is the Homebrew package name. The second is an existing
local project directory. The script creates
`~/develop/go/my-tool/.github/workflows/homebrew.yml`, ready to dispatch to
`mikeoertli/homebrew-tap` on its `main` branch. Names use lowercase letters,
digits, and hyphens. Python 3 is the only generator dependency.

An existing `homebrew.yml` is preserved by default. To deliberately replace it:

```sh
python3 scripts/generate-workflow.py my-tool ~/develop/go/my-tool --force
```

Before releasing a new package through this tap:

1. Add its source entry to `sources.json` and create its formula template in
   `templates/my-tool.rb.in`, following the existing formula templates.
2. Add the package name to the `formula` input choices in
   `.github/workflows/update.yml`, so the tap accepts the dispatched package.
3. Bootstrap its first published tag with
   `python3 scripts/update-formulas.py my-tool --tag v0.1.0`, validate the formula, and
   publish those tap changes. CI automatically includes registered public packages.
4. Add the project's `TAP_DISPATCH_TOKEN` repository secret. Commit the generated
   workflow and include it in the commit you tag for the next release.

Only future tag pushes that contain the workflow trigger notifications. Existing
tags are not rerun retroactively, and prerelease tags are skipped. The tap's
`update.yml` must be published on `main` before it can receive dispatches.
If an update PR is already open, the tap waits for it to be resolved; the daily
check picks up any remaining releases afterward.

### Release a project

Ordinary pushes to a project's default branch and local edits do not update the
tap automatically. Project dispatches and the scheduled workflow watch stable
version tags. When a new tag is detected, the tap opens an update PR; publishing
that PR's bottles and merging the update still require the maintainer step below. The schedule only
runs after this tap is pushed and its Actions secret is configured.

After the tap update is published, run `brew update` and `brew upgrade` on each
computer when you want the new version. Homebrew does not automatically replace
an installed executable just because a project has changed.

1. Publish a stable `vMAJOR.MINOR.PATCH` tag in the upstream repository using
   that project's release process.
2. Update the tap from that tag:

   ```sh
   cd ~/develop/go/homebrew-tap
   python3 scripts/update-formulas.py krm --tag v1.2.1
   make check
   ```

3. Review the formula and `sources.json` changes and open a tap pull request.
4. Wait for **brew test-bot** on macOS Apple Silicon, macOS Intel, and Linux.
5. Run **brew pr-pull** from the tap's Actions page with the PR number and the
   exact reviewed head commit SHA. This publishes bottles, updates their checksums
   in the formulas, and merges the package update. Do not merge the PR first if
   you want to publish its bottles through this workflow.

The updater resolves tags to immutable commits, calculates archive SHA-256
checksums, rejects downgrades, and checks that a tagged release matches its
embedded `VERSION` when one exists. Updating a snapshot to a tag of the same
version increments the Homebrew revision if the source changed. Upstream tags
should never be moved after publication.

To check the latest stable tags for all bootstrapped public projects:

```sh
python3 scripts/update-formulas.py --dry-run
python3 scripts/update-formulas.py
```

To explicitly package a newer unreleased source snapshot:

```sh
python3 scripts/update-formulas.py gprm --snapshot
```

Snapshots at the same version increment the package revision; bump the project's
`VERSION` before publishing substantial changes.

### Automatic release checks

The **Check upstream releases** workflow runs daily and can be dispatched
manually. It checks stable tags, opens a single update PR, and waits for review.
It skips private upstreams, projects not yet bootstrapped, prereleases, and tags
older than an already packaged snapshot version.

Set the repository Actions secret **TAP_UPDATE_TOKEN** to a fine-grained GitHub
token scoped to `mikeoertli/homebrew-tap`, with **Contents: Read and write** and
**Pull requests: Read and write**. A separate token allows bot-created PRs to
trigger the test/bottle workflow; PRs created with the default `GITHUB_TOKEN`
do not trigger those workflows. The secret is required when an update is found.
Normal release checks use the default read-only workflow token.

Bottle publishing uses the default `GITHUB_TOKEN` with job-scoped write
permissions. Repository rules may require allowing the publishing workflow to
push to `main`. Initial workflows cannot run until this tap is pushed to GitHub.

The publishing workflow follows Homebrew's `brew tap-new` templates. Its
platform matrix currently covers Apple Silicon macOS 26, Intel macOS 15, and
Linux. Other supported systems can build from source; expand the matrix as
needed. The first source-only commit has no bottles; publish a subsequent package
PR to produce them.

### Troubleshooting Actions failures

If **Check upstream releases** fails with HTTP 403 while pushing
`automation/releases`, GitHub rejected the updater's write access. Check the
fine-grained token stored as the tap repository's **TAP_UPDATE_TOKEN**: its
resource owner must be `mikeoertli`, its selected repository must include
`homebrew-tap`, and **Contents** and **Pull requests** must both have **Read and
write** access. Also check its expiration. The Actions-only dispatch token cannot
push formula updates. GitHub does not expose stored secret values for inspection;
replace the secret if you are unsure which token was saved.

After correcting the token, run **Check upstream releases → Run workflow** with
`formula: all` and the tag left blank. This catches up all four projects without
pushing their tags again.

The Intel CI job installs Homebrew's lint tools from available bottles, including
bottles built for an older macOS, to avoid building their dependencies from
source. Package builds and tests still run on the selected Intel macOS runner.
Failures fetching lint dependencies occur before any project is compiled.

### Local validation and template edits

```sh
make check
brew audit --strict mikeoertli/tap/krm
brew install --build-from-source mikeoertli/tap/krm
brew test mikeoertli/tap/krm
```

When developing the uncommitted tap locally, Homebrew needs to see it under its
tap directory. If the tap is not already installed, you can link this checkout:

```sh
mkdir -p "$(brew --repository)/Library/Taps/mikeoertli"
ln -s "$HOME/develop/go/homebrew-tap" "$(brew --repository)/Library/Taps/mikeoertli/homebrew-tap"
```

After editing templates, run `make render` and review the resulting formula
changes. Rendering intentionally removes existing bottle blocks; rebuild and
publish bottles for the changed definitions. Ordinary unchanged release checks
preserve existing bottle blocks. Keep formula-specific fixes in the templates
as well as the active files.
