# The Internet — Python Playwright tests

A Python Playwright end-to-end suite with 110 test cases covering all 76 demos
listed on the site's homepage, plus linked examples such as nested frames,
the iframe editor, shifting content, and HTTP status-code pages.

## Setup

Requires Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run

All tests:
```bash
python -m pytest
```

Specific test:
```bash
python -m pytest tests/test_authentication.py
```

## Coverage

| Test module | Demos and behaviors |
| --- | --- |
| `test_authentication.py` | Login, invalid credentials, logout |
| `test_checkboxes.py`, `test_dropdown.py`, `test_javascript_alerts.py` | Checkboxes, select options, alert/confirm/prompt handling |
| `test_dynamic_loading.py` | Both linked dynamic loading examples |
| `test_page_content.py` | Homepage filtering and coverage audit, A/B variants, accessibility fixes, broken images, challenging/deep DOM, disappearing elements, dynamic content, notifications, typos, visual variants |
| `test_interactions.py` | Add/remove elements, context menu, drag and drop, dynamic controls, entry/exit modals, floating menu, slider, hovers, number inputs, key presses, canvas, native dialogs, pointer gestures, responsive navigation, SVG, stale elements, toasts |
| `test_forms.py` | Autocomplete, Basic/Digest authentication, cookie consent, custom dropdown, date pickers, password recovery form, form validation, large form, multiple select, radio buttons, read-only controls, two-factor login |
| `test_frames_and_navigation.py` | Frames, TinyMCE, advanced iframes, simple/advanced shadow DOM, new windows, redirects, SPA history, subdirectories, all three shifting examples, sortable tables |
| `test_files.py` | File upload/download, authenticated download, generated downloads, jQuery UI nested menu |
| `test_network_and_browser.py` | Permissions/clipboard, geolocation, locale/timezone, SSE updates, WebSocket echo, two-user chat, JavaScript errors, network/console/CSP events, API failures/retries, slow resources, status codes, infinite scrolling, virtualized list |

Tests declare their homepage route with `@pytest.mark.covers("/path")`. The
homepage inventory test compares the live links with those declarations and fails
if a new demo has no declared test. This measures page coverage, not every possible
action or input on each page.

Random demos accept their documented variants. Broken images, JavaScript errors,
and HTTP error responses are asserted as intentional demo behavior. Visual
variants are checked through DOM/style changes rather than platform-specific
reference screenshots. Closed shadow roots are checked for encapsulation; their
internals are not accessed through Playwright locators. Exit intent uses a
synthetic document mouseleave because headless browsers have no browser chrome.

Password recovery verifies the form without submitting it or sending email.
Camera hardware is not required. Upload tests use a unique, harmless text file;
the public demo may retain uploaded fixtures. Chat tests use a unique room per
run to avoid interfering with other visitors or parallel workers. Geolocation is
emulated, downloads use pytest temporary directories, and contexts isolate cookies
and authentication state.

Run the expanded suite with Jenkins's four-worker setting locally:

```bash
python -m pytest -n 4 --junitxml=reports/junit.xml
```

No test-image rebuild is needed for these additional test files; the dependencies
are unchanged and Jenkins mounts the current checkout into the prepared image.

### Parallel execution

Enabled by default, number of workers is based on CPU cores for local runs. Jenkins
automatically uses four workers, configured by `WORKERS` in the Jenkinsfile's
`environment` block. The pipeline still publishes one combined JUnit report and archives
failure artifacts. `disableConcurrentBuilds()` prevents separate builds from
overlapping; it does not prevent workers inside one build from running in parallel.


Tests target https://the-internet.herokuapp.com by default and require network
access. To use another deployment, provide BASE_URL variable:

```bash
BASE_URL=http://localhost:8080 python -m pytest
```

Each test gets an isolated browser context through pytest-playwright. Tests use
Playwright's waiting assertions without fixed sleeps. Chromium runs headlessly by
default. Failure screenshots and traces are saved under `test-results/`.
Open a saved trace with:

```bash
python -m playwright show-trace test-results/<test-directory>/trace.zip
```

## Jenkins

The `Jenkinsfile` runs pytest and headless Chromium together inside the custom
`the-internet-playwright:latest` test image, based on the official Playwright Python
image. Jenkins itself can run on a host or in a
container; the test agent needs access to Docker.

### Jenkins setup

1. Put this project in a Git repository accessible to Jenkins.
2. Install the plugins listed in `jenkins/plugins.txt` (see below).
3. Provide a Linux Jenkins agent labelled `docker`, with Git, the Docker CLI,
   and permission to use its Docker daemon. The daemon must be able to mount the
   agent workspace. Build the test image on this agent's Docker daemon using the
   command below. Image builds need access to Ubuntu package repositories, PyPI,
   and Microsoft's container registry; test runs only need access to the target site.
4. Create a **Pipeline** job, choose **Pipeline script from SCM**, select Git,
   configure your repository and credentials, and use `Jenkinsfile` as the script path.
5. Run **Build Now**. Jenkins automatically uses four workers and
   `https://the-internet.herokuapp.com`, configured by `WORKERS` and `BASE_URL`
   in the Jenkinsfile's `environment` block. No build parameters are required.
   Configure an SCM webhook if you want builds on pushes.

The test image includes Python dependencies in `/opt/venv`. The pipeline uses
that environment directly, executes the suite without installing packages, and
publishes JUnit results in Jenkins. Failed tests fail the build. Screenshots and
traces are archived as downloadable build artifacts; passed tests discard them.
Runs have a 15-minute timeout and do not overlap for the same job.

The Playwright Python version in `requirements.txt` must match the base image
tag in the root `Dockerfile`. Update both together. The base image contains browsers
and their system libraries, so the pipeline does not download browsers again.
After changing Playwright versions locally, rerun `python -m playwright install chromium`.

### Building and running the test image

From the project directory, build the image before running Jenkins:

```bash
docker build -t the-internet-playwright:latest .
```

The Dockerfile installs `python3-venv`, creates `/opt/venv`, and installs the
requirements during the image build. Docker reuses these layers while their inputs
remain unchanged and the build cache is available. Rebuild after changing
`requirements.txt` or the Dockerfile. To deliberately refresh packages allowed by
the version ranges, rebuild with `--no-cache`. Test source changes do not require
an image rebuild because Jenkins mounts its checked-out workspace at runtime.
The root `.dockerignore` keeps local environments and test results out of the build
context.

The image must exist on the Docker daemon used by the selected Jenkins agent.
If you have several agents, publish it to a container registry and update the
`image` reference in `Jenkinsfile` to that registry image (prefer a versioned tag).

To reproduce the Jenkins test command locally:

```bash
docker run --rm --init --ipc=host \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e BASE_URL=https://the-internet.herokuapp.com \
  -v "$PWD:/work" -w /work \
  the-internet-playwright:latest \
  /opt/venv/bin/python -m pytest --junitxml=reports/junit.xml
```

The container uses the preinstalled environment without modifying it, so the
command works with the non-root user above. The mounted project retains reports
and failure artifacts after the container exits.

Docker is optional for Playwright itself. If your Jenkins agents cannot run Docker,
use a Linux agent with Python, install the requirements, then run
`python -m playwright install --with-deps chromium` before pytest. Installing
system dependencies requires suitable administrator permissions on that agent.

### Installing Jenkins plugins from a file

`jenkins/plugins.txt` lists plugin IDs, one per line:

| Plugin ID | Purpose |
| --- | --- |
| `workflow-aggregator` | Pipeline support, including Declarative Pipeline |
| `docker-workflow` | The `agent { docker { ... } }` syntax |
| `git` | Check out the repository |
| `junit` | Publish pytest's JUnit XML report |
| `timestamper` | The pipeline's `timestamps()` option |

The Jenkins Plugin Installation Manager installs their dependencies automatically.
Versions are currently unpinned; use `plugin-id:version` entries when you want
to maintain a tested set of plugin versions for a specific Jenkins release.

The separate `jenkins/Dockerfile` builds the Jenkins controller with plugins; the
root `Dockerfile` builds the Playwright test environment. To build the controller
image from the project directory:

```bash
docker build -t the-internet-jenkins ./jenkins
```

Use this image instead of `jenkins/jenkins` when provisioning your controller.
It installs the plugins during the image build; it does not configure jobs or
provide the Docker-capable test agent described above. Existing Jenkins volumes
may retain installed plugin versions, so check the plugin state after an image
upgrade.

If `jenkins-plugin-cli` is available in your controller environment, you can also
use the list directly as part of controller provisioning:

```bash
jenkins-plugin-cli --plugin-file jenkins/plugins.txt
```

This tool is bundled with the official Jenkins Docker image; it is not necessarily
installed on a host-based Jenkins controller. Its default destination in that image
is the reference plugins directory used at startup. Running it inside an already
running container does not immediately load plugins into the active controller.

The plugin list must be applied before Jenkins compiles `Jenkinsfile`. Merely
committing it to the repository does not install plugins, and the pipeline cannot
install the plugin needed to parse its own `docker` agent declaration.
