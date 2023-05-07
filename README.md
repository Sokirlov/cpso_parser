# This is system account validator  

This system used:
- Sherlock (for validate username in 300 socials sites)
- GHunt (for validate proposed User location)
- WhatsApp (validate if user had accounts)

## Download project 
For download use this command, because sherlock connect as submodule  
```shell
git clone --recurse-submodules https://github.com/Sokirlov/cpso_parser.git 
```


## How start system 
1. You need edit the web-variables.env file.
```yaml
GMAILID="Your active email on gmail.com"
PASSWORD="Password for gmail"
IPSERVER="Your IP-adress"
SOKEY="Password for secure connect to socket"

```
2. Download last the solenoid web-browser
```shell
docker pull selenoid/chrome
```
3. Start systems with docker-compose file with this command
```shell
docker-compose --env-file web-variables.env up --build
```
4. After system start you can you ws:// protocol to connect the server. 
For connect use ws://IP-adress_from_env_file:8765.

## How use system

1. Create connect with server socket. For this you need send in headers  key `secure` 
and as value, you need use the `value SOKEY  from your web-variables.env` 
2. In body you send request in JSON format
```json
{
    "types": "name" / "phone" / "email" / "capcha",
    "payload": "your request value",
    "social": "sherlock" / "whatsapp" / "ghunt" 
}
```



