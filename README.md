# Argos, Automated Real-time Guardian Observation System

ARGOS is a two-part system that allows to monitor public spaces in an autonomous manner, helping to ensure the security of the public:

1. **[argos_master](./argos/argos_master/README.md)**: This is the central unit of the ARGOS system, allowing to manage and control multiple `argos_node` instances. Furthermore, is this unit that is responsible to analyze the incoming video streams to detect security risks.
2. **[argos_node](./argos/argos_node/README.md)**:  Worker nodes resposible for capturing and streaming video from intel realsense cameras.

## License

ARGOS is released under the Argos Restricted License. See [LICENSE](LICENSE) for more details.
