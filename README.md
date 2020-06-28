# seattlefiretwitterbot

To build and run the Docker container, execute:

```
docker build .
docker run -p 8080:8080 -e PORT=8080 \
  -e API_KEY="${API_KEY?}" \
  -e API_KEY_SECRET="${API_KEY_SECRET?}" \
  -e ACCESS_TOKEN="${ACCESS_TOKEN?}" \
  -e ACCESS_TOKEN_SECRET="${ACCESS_TOKEN_SECRET?}" \
  "${IMAGE_ID?}"
```
