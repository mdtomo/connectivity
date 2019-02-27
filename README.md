[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
# Connectivity
Monitor the network connectivity between two machines and send SMS alerts when connectivity is lost. Connectivity works in client or server mode. The machine running Connectivity in client mode will send UDP packets, at regular intervals to the machine running Connectivity in server mode. If the machine running in server mode fails to receive UDP packets at the set regular interval, an SMS alert will be sent via Amazon Simple Notification Service (SNS).

## Installation
`git clone https://github.com/mdtomo/connectivity`

## Usage
To use Connectivity run `connectivity.py` on two machines (or the same machine for testing on localhost). In `config.py` set the monitoring/alerting machine to Mode.SERVER and the machine to be monitored to Mode.CLIENT'.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.