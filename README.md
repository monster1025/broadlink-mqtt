# Broadlink (SP2 and RM2) to MQTT bridge

Works with Broadlink WiFi plugs and RM2-Mini.
You need to edit you bulb IPs in main.py (not yet fixed).

Sample docker-compose.yml file:
```
main:
  build: .
  container_name: broadlink
  environment:
    - MQTT_SERVER=192.168.1.93
    - MQTT_USER=mqtt_user
    - MQTT_PASS=passw0rd
  restart: always
```

```
docker-compose build && docker-compose up -d
```

## Known bugs:
- Plug alive status updated only at startup.
- IP-Name list in main.py
- Bad code style =(