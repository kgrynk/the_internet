# The Internet — Python Playwright tests

A small end-to-end suite covering Form Authentication, Checkboxes, Dropdown,
Dynamic Loading, and JavaScript Alerts. The 15 test cases include invalid login
credentials, both dynamic loading examples, and accepting or dismissing dialogs.

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

The `Jenkinsfile` runs pytest and headless Chromium together inside the official
Playwright Python Docker image. Jenkins itself can run on a host or in a
container; the test agent needs access to Docker.

### Jenkins setup

1. Put this project in a Git repository accessible to Jenkins.
2. Install the plugins listed in `jenkins/plugins.txt` (see below).
3. Provide a Linux Jenkins agent labelled `docker`, with Git, the Docker CLI,
   and permission to use its Docker daemon. The daemon must be able to mount the
   agent workspace. The container needs outbound access to PyPI and the target site;
   the agent also needs access to Microsoft's container registry.
4. Create a **Pipeline** job, choose **Pipeline script from SCM**, select Git,
   configure your repository and credentials, and use `Jenkinsfile` as the script path.
5. Run **Build Now**. Later runs can use **Build with Parameters** to change
   `BASE_URL`. Configure an SCM webhook if you want builds on pushes.

The pipeline installs Python dependencies in `/tmp/the-internet-python` inside
the disposable container, exposes them through `PYTHONPATH`, executes the suite, and
publishes JUnit results in Jenkins. Failed tests fail the build. Screenshots and
traces are archived as downloadable build artifacts; passed tests discard them.
Runs have a 15-minute timeout and do not overlap for the same job.

The Playwright Python version in `requirements.txt` must match the Docker image
tag in `Jenkinsfile`. Update both together. The image already contains browsers
and their system libraries, so the pipeline does not download browsers again.
After changing Playwright versions locally, rerun `python -m playwright install chromium`.

To reproduce the Jenkins test command locally in Docker (from project directory):

```bash
docker run --rm --init --ipc=host \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e PYTHONPATH=/tmp/the-internet-python \
  -e BASE_URL=https://the-internet.herokuapp.com \
  -v "$PWD:/work" -w /work \
  mcr.microsoft.com/playwright/python:v1.64.1-noble \
  sh -c 'python -m pip install --no-cache-dir --target "$PYTHONPATH" -r requirements.txt && python -m pytest --junitxml=reports/junit.xml'
```

The container command does not create a virtual environment: this image may lack
`ensurepip`/`python3-venv`. Installing into a temporary directory also works with
the non-root user above, without writing to system Python directories. The mounted
project retains reports and failure artifacts after the container exits.

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

For a Jenkins controller built from the official Docker image, a Dockerfile is
provided. From the project directory, build it with:

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
