# iSpod
Requirements and dependencies
- Raspberry Pi Zero 2W
- Raspberry Pi OS Lite (64-bit)
- Raspotify

First steps:

**Actualizar lista de paquetes**

`sudo apt update`

**Actualizar el sistema completo**

`sudo apt full-upgrade -y`

**Eliminar paquetes obsoletos que ya no sirvan**

`sudo apt autoremove -y`

**Limpiar caché para liberar espacio en la SD**

`sudo apt clean`

**Install Git and Python**

`sudo apt install git python3-pip python3-venv -y`

### Raspotify

It is needed to install [Raspotify](https://github.com/dtcooper/raspotify) so the Raspberry can play music itself as a Spotify Connect device.

`sudo apt-get -y install curl && curl -sL https://dtcooper.github.io/raspotify/install.sh | sh`
