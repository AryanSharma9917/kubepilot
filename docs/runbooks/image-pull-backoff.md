# Image Pull Backoff

Use this runbook when pods are stuck in `ImagePullBackOff`, `ErrImagePull`, or
`InvalidImageName`.

## Signals

- Pod phase is `Pending` while container status reports an image pull failure.
- Events mention `Failed`, `BackOff`, `pull access denied`, or `manifest unknown`.
- The deployment has zero ready replicas even though pods are being created.

## Common Causes

- The image tag does not exist in the registry.
- The namespace is missing an image pull secret.
- The service account is not connected to the required registry credential.
- The node cannot reach the registry because of network policy or DNS failure.

## Checks

1. Inspect pod events for the exact registry error.
2. Compare the deployment image reference with the expected release artifact.
3. Confirm image pull secrets exist in the workload namespace.
4. Check whether the deployment service account references the pull secret.
5. Retry after fixing credentials or rolling out the corrected image tag.

## Operator Response

Treat image pull failures as release-blocking when no replicas are ready. Roll
back to the last known-good image if the corrected tag or registry credential is
not immediately available.
