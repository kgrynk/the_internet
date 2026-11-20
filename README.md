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
2. Install the Pipeline, Docker Pipeline, Git, and JUnit plugins in Jenkins.
3. Provide a Linux Jenkins agent labelled `docker`, with Git, the Docker CLI,
   and permission to use its Docker daemon. The daemon must be able to mount the
   agent workspace. The container needs outbound access to PyPI and the target site;
   the agent also needs access to Microsoft's container registry.
4. Create a **Pipeline** job, choose **Pipeline script from SCM**, select Git,
   configure your repository and credentials, and use `Jenkinsfile` as the script path.
5. Run **Build Now**. Later runs can use **Build with Parameters** to change
   `BASE_URL`. Configure an SCM webhook if you want builds on pushes.

The pipeline installs Python dependencies in `.venv-ci`, executes the suite, and
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
  -e BASE_URL=https://the-internet.herokuapp.com \
  -v "$PWD:/work" -w /work \
  mcr.microsoft.com/playwright/python:v1.64.1-noble \
  sh -c 'python -m venv --clear .venv-ci && .venv-ci/bin/python -m pip install --no-cache-dir -r requirements.txt && .venv-ci/bin/python -m pytest --junitxml=reports/junit.xml'
```

Docker is optional for Playwright itself. If your Jenkins agents cannot run Docker,
use a Linux agent with Python, install the requirements, then run
`python -m playwright install --with-deps chromium` before pytest. Installing
system dependencies requires suitable administrator permissions on that agent.
