# uhh-pd-ml/admin

Administrative infrastructure for the **UHH Particle Detector & Machine Learning** GitHub organization.

This repository contains automation and configuration for managing the GitHub organization. The goal is to keep organization administration reproducible, auditable, and under version control.

## Current functionality

### Team synchronization

The repository currently provides an automated workflow that synchronizes the `everyone` team with the organization's membership.

Whenever the workflow runs, it

* retrieves all members of the `uhh-pd-ml` GitHub organization,
* retrieves all members of the `everyone` team,
* adds organization members that are missing from the team, and
* removes users from the team if they are no longer members of the organization.

This allows repository permissions to be granted to the `everyone` team instead of maintaining access lists manually.

## Authentication

The workflow authenticates using a GitHub App rather than a personal access token.

Required repository configuration:

### Repository variables

| Name     | Description           |
| -------- | --------------------- |
| `APP_ID` | Numeric GitHub App ID |

### Repository secrets

| Name              | Description                                |
| ----------------- | ------------------------------------------ |
| `APP_PRIVATE_KEY` | Private key (PEM format) of the GitHub App |

The workflow creates a short-lived installation token at runtime using the GitHub App and uses this token to interact with the GitHub API.

## Running the synchronization

### Automatically

The workflow runs on a daily schedule.

### Manually

From the GitHub web interface:

1. Open the **Actions** tab.
2. Select **Sync everyone team**.
3. Click **Run workflow**.

This is useful after adding or removing organization members.

## Required GitHub App permissions

The GitHub App should be installed on the `uhh-pd-ml` organization and granted permissions sufficient to

* read organization members,
* read team membership,
* modify team membership.

The app only needs access to this repository.

