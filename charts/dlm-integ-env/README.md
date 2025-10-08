# SKA DLM Integration Environment

* This is a work in progress*

The templates provided allow for the setup/creation of the following compoenents of a
system integration environment:

* PVCs - one each for daq, pst and sdp.
* PVC - one for the destination storage endpoint.
* ssh key secrets - one for each component of the system. They are taken from the files/keys
  directory. See the README.md in that directory for more details.

## Notes on template reuse

This chart now declares a local dependency on the `ska-dlm-client` chart (via `file://../ska-dlm-client`).
It reuses that chart's named templates (e.g., `ska-dlm-client.ssh-storage-access.*`) without copying them.
All services in `ska-dlm-client` are disabled by default, so adding the dependency does not render additional
resources unless explicitly enabled. The `dlm-integ-env` templates include those shared templates as needed.
