<div align="center">

# **Konnex Chain SDK** <!-- omit in toc -->
[GitLab (Development)](https://git.konnex.world/)

---

## Robotics Permissionless Market SDK <!-- omit in toc -->

[Konnex Docs](https://docs.konnex.world/) • [Architecture](https://docs.konnex.world/docs/protocol-architecture) • [Robotic AI SubNets](https://docs.konnex.world/robotic-ai-subnets/overview) • [SDK Overview](https://docs.konnex.world/sdk/overview)

</div>

- [Overview of Konnex Chain SDK](#overview-of-konnex-chain-sdk)
- [How This Relates to Bittensor](#how-this-relates-to-bittensor)
- [Konnex Robotics Flow](#konnex-robotics-flow)
- [Protocol and Product Docs](#protocol-and-product-docs)
- [Release Notes](#release-notes)
- [Install Konnex Chain SDK](#install-konnex-chain-sdk)
- [Upgrade](#upgrade)
- [Install on macOS and Linux](#install-on-macos-and-linux)
  - [Install using a Bash command](#install-using-a-bash-command)
  - [Install using `pip3 install`](#install-using-pip3-install)
  - [Install from source](#install-from-source)
  - [Verify using Python interpreter](#verify-using-python-interpreter)
  - [Verify by listing axon information](#verify-by-listing-axon-information)
- [Release Guidelines](#release-guidelines)
- [Contributions](#contributions)
- [Acknowledgments](#acknowledgments)

---

## Overview of Konnex Chain SDK

`konnex-chain-sdk` is a Konnex-focused SDK fork built on top of the Bittensor codebase and Subtensor interaction model. It keeps Bittensor compatibility while adding Konnex-specific chain and product workflows around robotics AI, task-scoped operations, and PoPW-style execution flows.

## How This Relates to Bittensor

This repository started from upstream `opentensor/bittensor` and continues to use its core primitives (wallet, subtensor/subnets, chain querying, and extrinsics). Konnex changes are layered on top for:

- task-scoped APIs (`subnet_id` + `task_id`) used by Konnex robotics workloads,
- integration hooks for robotics execution and verification flows,
- Konnex-oriented docs and product semantics.

Upstream source and history: [opentensor/bittensor](https://github.com/opentensor/bittensor).

---

## Konnex Robotics Flow

Konnex positions the network as a permissionless market for robotics AI and verifiable physical work:

1. A task is broadcast to competing AI policy providers.
2. Verifiers evaluate outputs and rank policy quality.
3. The selected policy is executed in physical or simulated robotics environments.
4. Outcomes are validated as proof-of-execution and settled on-chain.

This SDK is the chain-facing toolkit that supports those task, verification, and settlement paths in code.

## Protocol and Product Docs

- Konnex docs home: [docs.konnex.world](https://docs.konnex.world/)
- Protocol architecture: [Protocol Architecture](https://docs.konnex.world/docs/protocol-architecture)
- Robot contracts and PoPW: [Robot-to-Robot Contracts & PoPW](https://docs.konnex.world/docs/robot-to-robot-contracts-and-popw)
- SDK docs area: [SDK Overview](https://docs.konnex.world/sdk/overview)

## Task-Scoped API Surface

Recent Konnex SDK extensions standardize task-scoped chain access using `(subnet_id, task_id)`:

- `task_scope_params*` helpers for canonical query param tuples.
- `query_subtensor_for_task*` and `query_map_subtensor_for_task*` for Subtensor storage access.
- `query_module_for_task*` for module-level task-scoped queries with extra params.
- `compose_call_for_task*` and `sign_and_send_extrinsic_for_task*` for task-scoped extrinsics.
- `Escrow` helper methods for task-scoped escrow compose/submit/query flows.

All `*from_scope` variants accept a pre-built `TaskScope` object for safer composition in higher-level workflows.

### Escrow Helper Preview

```python
api = bt.SubtensorApi(network="konnex-testnet")

# compose extrinsic calls
call = api.create_escrow_call(
    subnet_id=1,
    task_id="task-42",
    payer="5F...",
    payee="5G...",
    amount_rao=1_000_000_000,
    timeout_blocks=1200,
)

# query by task scope
escrow_state = api.query_escrow_by_task(subnet_id=1, task_id="task-42")
events = api.query_escrow_events_by_task(subnet_id=1, task_id="task-42")
```

### PoPW Helper Preview

```python
api = bt.SubtensorApi(network="konnex-testnet")

vote_call = api.popw_vote_call(
    subnet_id=1,
    task_id="task-42",
    vote=True,
    report_hash="0x...",
    confidence_bps=9500,
)

status = api.query_popw_status_by_task(subnet_id=1, task_id="task-42")
votes = api.query_popw_votes_by_task(subnet_id=1, task_id="task-42")
```

### Settlement Orchestration Preview

```python
api = bt.SubtensorApi(network="konnex-testnet")
snapshot = api.settlement_snapshot(subnet_id=1, task_id="task-42")

if api.can_release_by_popw(subnet_id=1, task_id="task-42"):
    release_call = api.guarded_release_call(
        subnet_id=1,
        task_id="task-42",
        escrow_id=123,
    )

normalized = api.normalize_popw_status(snapshot["popw_status"])
print(normalized.decision.value, normalized.releasable)
```

## Konnex Network Profiles

The SDK now exposes named network profiles for Konnex environments:

- `konnex-devnet`
- `konnex-testnet`

Profiles include endpoint defaults plus fallback/archive endpoint sets and are available from:

- `bittensor.core.settings.get_konnex_network_profile(...)`
- `SubtensorApi.get_konnex_network_profile(...)`

`SubtensorApi` now auto-applies profile fallback/archive defaults when initialized with
`network="konnex-devnet"` or `network="konnex-testnet"` (unless explicitly overridden).

You can also enforce runtime compatibility in client code:

```python
api = bt.SubtensorApi(network="konnex-testnet")
api.ensure_min_spec_version(1000)
```

## Legacy Bittensor Notes

Large parts of install and test instructions below still reference upstream Bittensor naming and tooling. Keep that in mind while Konnex-specific docs are expanded.

## Release Notes

See [Bittensor SDK Release Notes](https://docs.bittensor.com/bittensor-rel-notes).

---

## Install Konnex Chain SDK

Before you can start developing, install the SDK and then create a wallet.

## Upgrade

If you already installed the SDK, upgrade to the latest version:

```bash
python3 -m pip install --upgrade bittensor
```

---

## Install on macOS and Linux

You can install Konnex Chain SDK on your local machine in either of the following ways. **Make sure you verify your installation after installation**:
- [Install using a Bash command](#install-using-a-bash-command).
- [Install using `pip3 install`](#install-using-pip3-install)
- [Install from source](#install-from-source)

### Install using a Bash command

This is the most straightforward method. It is recommended for a beginner as it will pre-install requirements like Python, if they are not already present on your machine. Copy and paste the following `bash` command into your terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/opentensor/bittensor/master/scripts/install.sh)"
```

**For Ubuntu-Linux users**
If you are using Ubuntu-Linux, the script will prompt for `sudo` access to install all required apt-get packages.

### Install using `pip3 install`

```bash
python3 -m venv bt_venv
source bt_venv/bin/activate
pip install bittensor
```

### Install from source

1. Create and activate a virtual environment

    - Create Python virtual environment. Follow [this guide on python.org](https://docs.python.org/3/library/venv.html#creating-virtual-environments).

    - Activate the new environment. Follow [this guide on python.org](https://docs.python.org/3/library/venv.html#how-venvs-work)

2. Clone the Bittensor SDK repo

```bash
git clone https://github.com/opentensor/bittensor.git
```

3.  Install

You can install using any of the below options:

- **Install SDK**: Run the below command to install Bittensor SDK in the above virtual environment. This will also install `btcli`.

    ```python
    pip install bittensor
    ```

- **Install SDK with `torch`**: Install Bittensor SDK with [`torch`](https://pytorch.org/docs/stable/torch.html).

   ```python
    pip install bittensor[torch]
    ```
  In some environments the above command may fail, in which case run the command with added quotes as shown below:

  ```python
    pip install "bittensor[torch]"
    ```

- **Install SDK with `cubit`**: Install Bittensor SDK with [`cubit`](https://github.com/opentensor/cubit).

  1. Install `cubit` first. See the [Install](https://github.com/opentensor/cubit?tab=readme-ov-file#install) section. **Only Python 3.9 and 3.10 versions are supported**. 
  2. Then install SDK with `pip install bittensor`.
  
---

## Install on Windows

To install and run Bittensor SDK on Windows you must install [**WSL 2** (Windows Subsystem for Linux)](https://learn.microsoft.com/en-us/windows/wsl/about) on Windows and select [Ubuntu Linux distribution](https://github.com/ubuntu/WSL/blob/main/docs/guides/install-ubuntu-wsl2.md). 

After you installed the above, follow the same installation steps described above in [Install on macOS and Linux](#install-on-macos-and-linux).

**ALERT**: **Limited support on Windows**
While wallet transactions like delegating, transfer, registering, staking can be performed on a Windows machine using WSL 2, the mining and validating operations are not recommended and are not supported on Windows machines.

---

## Verify the installation

You can verify your installation in either of the below ways:

### Verify using `btsdk` version

```bash
python3 -m bittensor
```

The above command will show you the version of the `btsdk` you just installed.

### Verify using Python interpreter

1. Launch the Python interpreter on your terminal.   

    ```bash
    python3
    ```
2. Enter the following two lines in the Python interpreter.
   
    ```python
    import bittensor as bt
    print( bt.__version__ )
    ```
    The Python interpreter output will look like below:

    ```python
    Python 3.11.6 (main, Oct  2 2023, 13:45:54) [Clang 15.0.0 (clang-1500.0.40.1)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import bittensor as bt
    >>> print( bt.__version__ )
    <version number>
    ```
You will see the version number you installed in place of `<version number>`. 

### Verify by listing axon information

You can also verify the Bittensor SDK installation by listing the axon information for the neurons. Enter the following lines in the Python interpreter.

```python
import bittensor
metagraph = bittensor.Metagraph(1)
metagraph.axons[:10]
```
The Python interpreter output will look like below.

```bash
[AxonInfo( /ipv4/3.139.80.241:11055, 5GqDsK6SAPyQtG243hbaKTsoeumjQQLhUu8GyrXikPTmxjn7, 5D7u5BTqF3j1XHnizp9oR67GFRr8fBEFhbdnuVQEx91vpfB5, 600 ), AxonInfo( /ipv4/8.222.132.190:5108, 5CwqDkDt1uk2Bngvf8avrapUshGmiUvYZjYa7bfA9Gv9kn1i, 5HQ9eTDorvovKTxBc9RUD22FZHZzpy1KRfaxCnRsT9QhuvR6, 600 ), AxonInfo( /ipv4/34.90.71.181:8091, 5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2, 5ChuGqW2cxc5AZJ29z6vyTkTncg75L9ovfp8QN8eB8niSD75, 601 ), AxonInfo( /ipv4/64.247.206.79:8091, 5HK5tp6t2S59DywmHRWPBVJeJ86T61KjurYqeooqj8sREpeN, 5E7W9QXNoW7se7B11vWRMKRCSWkkAu9EYotG5Ci2f9cqV8jn, 601 ), AxonInfo( /ipv4/51.91.30.166:40203, 5EXYcaCdnvnMZbozeknFWbj6aKXojfBi9jUpJYHea68j4q1a, 5CsxoeDvWsQFZJnDCyzxaNKgA8pBJGUJyE1DThH8xU25qUMg, 601 ), AxonInfo( /ipv4/149.137.225.62:8091, 5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3, 5Ccmf1dJKzGtXX7h17eN72MVMRsFwvYjPVmkXPUaapczECf6, 600 ), AxonInfo( /ipv4/38.147.83.11:8091, 5Hddm3iBFD2GLT5ik7LZnT3XJUnRnN8PoeCFgGQgawUVKNm8, 5DCQw11aUW7bozAKkB8tB5bHqAjiu4F6mVLZBdgJnk8dzUoV, 610 ), AxonInfo( /ipv4/38.147.83.30:41422, 5HNQURvmjjYhTSksi8Wfsw676b4owGwfLR2BFAQzG7H3HhYf, 5EZUTdAbXyLmrs3oiPvfCM19nG6oRs4X7zpgxG5oL1iK4MAh, 610 ), AxonInfo( /ipv4/54.227.25.215:10022, 5DxrZuW8kmkZPKGKp1RBVovaP5zHtPLDHYc5Yu82Z1fWqK5u, 5FhXUSmSZ2ec7ozRSA8Bg3ywmGwrjoLLzsXjNcwmZme2GcSC, 601 ), AxonInfo( /ipv4/52.8.243.76:40033, 5EnZN591jjsKKbt3yBtfGKWHxhxRH9cJonqTKRT5yTRUyNon, 5ChzhHyGmWwEdHjuvAxoUifHEZ6xpUjR67fDd4a42UrPysyB, 601 )]
>>>
```

### Testing
You can run integration and unit tests in interactive mode of IDE or in terminal mode using the command:
```bash
pytest tests/integration_tests
pytest tests/unit_tests
```

#### E2E tests have 2 options for launching (legacy runner):
- using a compiler based on the substrait code
- using an already built docker image (docker runner)

#### Local environment variables:
- `LOCALNET_SH_PATH` - path to `localnet.sh` script in cloned subtensor repository (for legacy runner);
- `BUILD_BINARY` - (`=0` or `=1`) - used with `LOCALNET_SH_PATH` for build or not before start localnet node (for legacy runner);
- `USE_DOCKER` - (`=0` or `=1`) - used if you want to use specific runner to run e2e tests (for docker runner);
- `FAST_BLOCKS` - (`=0` or `=1`) - allows you to run a localnet node in fast or non-fast blocks mode (for both types of runers).

#### Using `docker runner` (default for now):
- E2E tests with docker image do not require preliminary compilation
- are executed very quickly
- require docker installed in OS

How to use:
```bash
pytest tests/e2e_tests
```

#### Using `legacy runner`:
- Will start compilation of the collected code in your subtensor repository
- you must provide the `LOCALNET_SH_PATH` variable in the local environment with the path to the file `/scripts/localnet.sh` in the cloned repository within your OS
- you can use the `BUILD_BINARY=0` variable, this will skip the copy step for each test.
- you can use the `USE_DOCKER=0` variable, this will run tests using the "legacy runner", even if docker is installed in your OS

#### How to use:
Regular e2e tests run
```bash
LOCALNET_SH_PATH=/path/to/your/localnet.sh pytest tests/e2e_tests
```

If you want to skip re-build process for each e2e test
```bash
BUILD_BINARY=0 LOCALNET_SH_PATH=/path/to/your/localnet.sh pytest tests/e2e_tests
```

If you want to use legacy runner even with installed Docker in your OS
```bash
USE_DOCKER=0 BUILD_BINARY=0 LOCALNET_SH_PATH=/path/to/your/localnet.sh pytest tests/e2e_tests
```

---

## Release Guidelines
Instructions for the release manager: [RELEASE_GUIDELINES.md](./contrib/RELEASE_GUIDELINES.md) document.

## Contributions
Ready to contribute? Read the [contributing guide](./contrib/CONTRIBUTING.md) before making a pull request.

## Acknowledgments
**learning-at-home/hivemind**
